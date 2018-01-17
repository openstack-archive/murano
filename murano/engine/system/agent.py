# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import datetime
import os
import os.path
import time
import uuid

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
import eventlet.event
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import base64
import six
from yaql import specs

import murano.common.exceptions as exceptions
from murano.common.messaging import message
from murano.dsl import dsl
import murano.engine.system.common as common

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class AgentException(Exception):
    pass


@dsl.name('io.murano.system.Agent')
class Agent(object):
    def __init__(self, host):
        self._enabled = False
        if CONF.engine.disable_murano_agent:
            LOG.debug('Use of murano-agent is disallowed '
                      'by the server configuration')
        self._host = host
        self._enabled = not CONF.engine.disable_murano_agent
        env = host.find_owner('io.murano.Environment')
        self._queue = str('e%s-h%s' % (env.id, host.id)).lower()
        self._signing_key = None
        if CONF.engine.signing_key:
            key_path = os.path.expanduser(CONF.engine.signing_key)
            if not os.path.exists(key_path):
                LOG.warn("Key file %s does not exist. "
                         "Message signing is disabled")
            else:
                with open(key_path, "rb") as key_file:
                    key_data = key_file.read()
                    self._signing_key = serialization.load_pem_private_key(
                        key_data, password=None, backend=default_backend())
        self._last_stamp = 0
        self._initialized = False

    @property
    def enabled(self):
        return self._enabled

    @specs.parameter('line_prefix', specs.yaqltypes.String())
    def signing_key(self, line_prefix=''):
        if not self._signing_key:
            return ""
        key = self._signing_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.PKCS1)
        return line_prefix + line_prefix.join(key.splitlines(True))

    def _initialize(self):
        if self._initialized:
            return

        # (sjmc7) - turn this into a no-op if agents are disabled
        if CONF.engine.disable_murano_agent:
            LOG.debug('Use of murano-agent is disallowed '
                      'by the server configuration')
        else:
            region = dsl.MuranoObjectInterface.create(self._host().getRegion())
            with common.create_rmq_client(region) as client:
                client.declare(self._queue, enable_ha=True, ttl=86400000)
        self._initialized = True

    def queue_name(self):
        return self._queue

    def _check_enabled(self):
        if CONF.engine.disable_murano_agent:
            raise exceptions.PolicyViolationException(
                'Use of murano-agent is disallowed '
                'by the server configuration')

    def _prepare_message(self, template, msg_id):
        msg = message.Message()
        msg.body = template
        msg.id = msg_id
        return msg

    def _send(self, template, wait_results, timeout):
        """Send a message over the MQ interface."""
        self._initialize()
        region = self._host().getRegion()
        msg_id = template.get('ID', uuid.uuid4().hex)
        if wait_results:
            event = eventlet.event.Event()
            listener = region['agentListener']
            listener().subscribe(msg_id, event)

        msg = self._prepare_message(template, msg_id)
        with common.create_rmq_client(region) as client:
            client.send(message=msg, key=self._queue, signing_func=self._sign)
        if wait_results:
            try:
                with eventlet.Timeout(timeout):
                    result = event.wait()

            except eventlet.Timeout:
                listener().unsubscribe(msg_id)
                raise exceptions.TimeoutException(
                    'The murano-agent did not respond '
                    'within {0} seconds'.format(timeout))

            if not result:
                return None

            if result.get('FormatVersion', '1.0.0').startswith('1.'):
                return self._process_v1_result(result)

            else:
                return self._process_v2_result(result)

        else:
            return None

    @specs.parameter(
        'resources', dsl.MuranoObjectParameter('io.murano.system.Resources'))
    def call(self, template, resources, timeout=None):
        if timeout is None:
            timeout = CONF.engine.agent_timeout
        self._check_enabled()
        plan = self.build_execution_plan(template, resources())
        return self._send(plan, True, timeout)

    @specs.parameter(
        'resources', dsl.MuranoObjectParameter('io.murano.system.Resources'))
    def send(self, template, resources):
        self._check_enabled()
        plan = self.build_execution_plan(template, resources())
        return self._send(plan, False, 0)

    def call_raw(self, plan, timeout=None):
        if timeout is None:
            timeout = CONF.engine.agent_timeout
        self._check_enabled()
        return self._send(plan, True, timeout)

    def send_raw(self, plan):
        self._check_enabled()
        return self._send(plan, False, 0)

    def is_ready(self, timeout=100):
        try:
            self.wait_ready(timeout)
        except exceptions.TimeoutException:
            return False
        else:
            return True

    def wait_ready(self, timeout=100):
        self._check_enabled()
        template = {'Body': 'return', 'FormatVersion': '2.0.0', 'Scripts': {}}
        self.call_raw(template, timeout)

    def _sign(self, msg):
        if not self._signing_key:
            return None
        return self._signing_key.sign(
            (self._queue + msg).encode('utf-8'),
            padding.PKCS1v15(), hashes.SHA256())

    def _process_v1_result(self, result):
        if result['IsException']:
            raise AgentException(dict(self._get_exception_info(
                result.get('Result', [])), source='execution_plan'))
        else:
            results = result.get('Result', [])
            if not result:
                return None
            value = results[-1]
            if value['IsException']:
                raise AgentException(dict(self._get_exception_info(
                    value.get('Result', [])), source='command'))
            else:
                return value.get('Result')

    def _process_v2_result(self, result):
        error_code = result.get('ErrorCode', 0)
        if not error_code:
            return result.get('Body')
        else:
            body = result.get('Body') or {}
            err = {
                'message': body.get('Message'),
                'details': body.get('AdditionalInfo'),
                'errorCode': error_code,
                'time': result.get('Time')
            }
            for attr in ('Message', 'AdditionalInfo'):
                if attr in body:
                    del body[attr]
            err['extra'] = body if body else None
            raise AgentException(err)

    def _get_array_item(self, array, index):
        return array[index] if len(array) > index else None

    def _get_exception_info(self, data):
        data = data or []
        return {
            'type': self._get_array_item(data, 0),
            'message': self._get_array_item(data, 1),
            'command': self._get_array_item(data, 2),
            'details': self._get_array_item(data, 3),
            'timestamp': datetime.datetime.now().isoformat()
        }

    def build_execution_plan(self, template, resources):
        template = copy.deepcopy(template)
        if not isinstance(template, dict):
            raise ValueError('Incorrect execution plan ')
        format_version = template.get('FormatVersion')
        if not format_version or format_version.startswith('1.'):
            return self._build_v1_execution_plan(template, resources)
        else:
            return self._build_v2_execution_plan(template, resources)

    def _generate_stamp(self):
        stamp = int(time.time() * 10000)
        if stamp <= self._last_stamp:
            stamp = self._last_stamp + 1
        self._last_stamp = stamp
        return stamp

    def _build_v1_execution_plan(self, template, resources):
        scripts_folder = 'scripts'
        script_files = template.get('Scripts', [])
        scripts = []
        for script in script_files:
            script_path = os.path.join(scripts_folder, script)
            scripts.append(base64.encode_as_text(
                resources.string(script_path, binary=True),
                encoding='latin1'))
        template['Scripts'] = scripts
        template['Stamp'] = self._generate_stamp()
        return template

    def _build_v2_execution_plan(self, template, resources):
        scripts_folder = 'scripts'
        plan_id = uuid.uuid4().hex
        template['ID'] = plan_id
        template['Stamp'] = self._generate_stamp()

        if 'Action' not in template:
            template['Action'] = 'Execute'
        if 'Files' not in template:
            template['Files'] = {}

        files = {}
        for file_id, file_descr in template['Files'].items():
            files[file_descr['Name']] = file_id

        for name, script in template.get('Scripts', {}).items():
            if 'EntryPoint' not in script:
                raise ValueError('No entry point in script ' + name)

            if 'Application' == script['Type']:
                if script['EntryPoint'] not in files:
                    script['EntryPoint'] = self._place_file(
                        scripts_folder, script['EntryPoint'],
                        template, resources, files)
                else:
                    script['EntryPoint'] = files[script['EntryPoint']]
            if 'Files' in script:
                for i, file in enumerate(script['Files']):
                    if self._get_name(file) not in files:
                        script['Files'][i] = self._place_file(
                            scripts_folder, file, template, resources, files)
                    else:
                        script['Files'][i] = files[file]
        return template

    def _is_url(self, file):
        file = self._get_url(file)
        parts = six.moves.urllib.parse.urlsplit(file)
        if not parts.scheme or not parts.netloc:
            return False
        else:
            return True

    def _get_url(self, file):
        if isinstance(file, dict):
            return list(file.values())[0]
        else:
            return file

    def _get_name(self, file):
        if isinstance(file, dict):
            name = list(file.keys())[0]
        else:
            name = file

        if self._is_url(name):
            name = name[name.rindex('/') + 1:len(name)]
        elif name.startswith('<') and name.endswith('>'):
            name = name[1: -1]
        return name

    def _get_file_value(self, file):
        if isinstance(file, dict):
            file = list(file.values())[0]
        return file

    def _get_body(self, file, resources, folder):
        use_base64 = self._is_base64(file)
        if use_base64:
            path = os.path.join(folder, file[1: -1])
            body = resources.string(path, binary=True)
            body = base64.encode_as_text(body) + "\n"
        else:
            path = os.path.join(folder, file)
            body = resources.string(path)
        return body

    def _is_base64(self, file):
        return file.startswith('<') and file.endswith('>')

    def _get_body_type(self, file):
        return 'Base64' if self._is_base64(file) else 'Text'

    def _place_file(self, folder, file, template, resources, files):
        file_value = self._get_file_value(file)
        name = self._get_name(file)
        file_id = uuid.uuid4().hex

        if self._is_url(file_value):
            template['Files'][file_id] = self._get_file_des_downloadable(file)
            files[name] = file_id

        else:
            template['Files'][file_id] = self._get_file_description(
                file, resources, folder)
            files[name] = file_id
        return file_id

    def _get_file_des_downloadable(self, file):
        name = self._get_name(file)
        file = self._get_file_value(file)
        return {
            'Name': str(name),
            'URL': file,
            'Type': 'Downloadable'
        }

    def _get_file_description(self, file, resources, folder):
        name = self._get_name(file)
        file_value = self._get_file_value(file)

        body_type = self._get_body_type(file_value)
        body = self._get_body(file_value, resources, folder)
        return {
            'Name': name,
            'BodyType': body_type,
            'Body': body
        }
