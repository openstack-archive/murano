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

import datetime
import os
import types
import uuid

import eventlet.event

from muranoapi.common import messaging
from muranoapi.engine import classes
from muranoapi.engine import objects
from muranoapi.engine.system import common
from muranoapi.engine import yaql_expression


class AgentException(Exception):
    def __init__(self, message_info):
        self.message_info = message_info


@classes.classname('org.openstack.murano.system.Agent')
class Agent(objects.MuranoObject):
    def initialize(self, _context, host):
        environment = yaql_expression.YaqlExpression(
            "$host.find('org.openstack.murano.Environment').require()"
        ).evaluate(_context)

        self._queue = str('e%s-h%s' % (
            environment.object_id, host.object_id)).lower()
        self._environment = environment

    def queueName(self):
        return self._queue

    def _send(self, template, wait_results):

        msg_id = template.get('ID', uuid.uuid4().hex)
        if wait_results:
            event = eventlet.event.Event()
            listener = self._environment.agentListener
            listener.subscribe(msg_id, event)
            listener.start()

        msg = messaging.Message()
        msg.body = template
        msg.id = msg_id

        with common.create_rmq_client() as client:
            client.declare(self._queue, enable_ha=True, ttl=86400000)
            client.send(message=msg, key=self._queue)

        if wait_results:
            result = event.wait()

            if not result:
                return None

            if result.get('FormatVersion', '1.0.0').startswith('1.'):
                return self._process_v1_result(result)
            else:
                return self._process_v2_result(result)
        else:
            return None

    def call(self, template, resources):
        plan = self.buildExecutionPlan(template, resources)
        return self._send(plan, True)

    def send(self, template, resources):
        plan = self.buildExecutionPlan(template, resources)
        return self._send(plan, False)

    def callRaw(self, plan):
        return self._send(plan, True)

    def sendRaw(self, plan):
        return self._send(plan, False)

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

    def buildExecutionPlan(self, template, resources):
        if not isinstance(template, types.DictionaryType):
            raise ValueError('Incorrect execution plan ')
        format_version = template.get('FormatVersion')
        if not format_version or format_version.startswith('1.'):
            return self._build_v1_execution_plan(template, resources)
        else:
            return self._build_v2_execution_plan(template, resources)

    def _build_v1_execution_plan(self, template, resources):
        scripts_folder = 'scripts'
        script_files = template.get('Scripts', [])
        scripts = []
        for script in script_files:
            script_path = os.path.join(scripts_folder, script)
            scripts.append(resources.string(
                script_path).encode('base64'))
        template['Scripts'] = scripts
        return template

    def _build_v2_execution_plan(self, template, resources):
        scripts_folder = 'scripts'
        plan_id = uuid.uuid4().hex
        template['ID'] = plan_id
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
            script['EntryPoint'] = self._place_file(
                scripts_folder, script['EntryPoint'],
                template, files, resources)
            if 'Files' in script:
                for i in range(0, len(script['Files'])):
                    script['Files'][i] = self._place_file(
                        scripts_folder, script['Files'][i],
                        template, files, resources)

        return template

    def _place_file(self, folder, name, template, files, resources):
        use_base64 = False
        if name.startswith('<') and name.endswith('>'):
            use_base64 = True
            name = name[1:len(name) - 1]
        if name in files:
            return files[name]

        file_id = uuid.uuid4().hex
        body_type = 'Base64' if use_base64 else 'Text'
        body = resources.string(os.path.join(folder, name))
        if use_base64:
            body = body.encode('base64')

        template['Files'][file_id] = {
            'Name': name,
            'BodyType': body_type,
            'Body': body
        }
        files[name] = file_id
        return file_id
