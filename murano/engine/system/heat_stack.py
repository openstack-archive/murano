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
import json

import eventlet
import heatclient.client as hclient
import heatclient.exc as heat_exc
from oslo_config import cfg
from oslo_log import log as logging

from murano.common import auth_utils
from murano.common.helpers import token_sanitizer
from murano.dsl import dsl
from murano.dsl import helpers
from murano.dsl import session_local_storage

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

HEAT_TEMPLATE_VERSION = '2013-05-23'


class HeatStackError(Exception):
    pass


@dsl.name('io.murano.system.HeatStack')
class HeatStack(object):
    def __init__(self, name, description=None, region_name=None):
        self._name = name
        self._template = None
        self._parameters = {}
        self._files = {}
        self._hot_environment = {}
        self._applied = True
        self._description = description
        self._last_stack_timestamps = (None, None)
        self._tags = ''
        self._region_name = region_name
        self._push_thread = None

    def _is_push_thread_alive(self):
        return self._push_thread is not None and not self._push_thread.dead

    def _kill_push_thread(self):
        if self._is_push_thread_alive():
            self._push_thread.cancel()
            self._wait_push_thread()

    def _wait_push_thread(self):
        if not self._is_push_thread_alive():
            return
        self._push_thread.wait()

    @staticmethod
    def _create_client(session, region_name):
        parameters = auth_utils.get_session_client_parameters(
            service_type='orchestration', region=region_name,
            conf='heat', session=session)
        return hclient.Client('1', **parameters)

    @property
    def _client(self):
        return self._get_client(self._region_name)

    @staticmethod
    @session_local_storage.execution_session_memoize
    def _get_client(region_name):
        session = auth_utils.get_client_session(conf='heat')
        return HeatStack._create_client(session, region_name)

    def _get_token_client(self):
        ks_session = auth_utils.get_token_client_session(conf='heat')
        return self._create_client(ks_session, self._region_name)

    def current(self):
        if self._template is not None:
            return self._template
        try:
            stack_info = self._client.stacks.get(stack_id=self._name)
            template = self._client.stacks.template(
                stack_id='{0}/{1}'.format(
                    stack_info.stack_name,
                    stack_info.id))
            self._template = template
            self._parameters.update(
                HeatStack._remove_system_params(stack_info.parameters))
            self._applied = True
            return self._template.copy()
        except heat_exc.HTTPNotFound:
            self._applied = True
            self._template = {}
            self._parameters.clear()
            return {}

    def parameters(self):
        self.current()
        return self._parameters.copy()

    def reload(self):
        self._template = None
        self._parameters.clear()
        return self.current()

    def set_template(self, template):
        self._template = template
        self._parameters.clear()
        self._applied = False

    def set_parameters(self, parameters):
        self._parameters = parameters
        self._applied = False

    def set_files(self, files):
        self._files = files
        self._applied = False

    def set_hot_environment(self, hot_environment):
        self._hot_environment = hot_environment
        self._applied = False

    def update_template(self, template):
        template_version = template.get('heat_template_version',
                                        HEAT_TEMPLATE_VERSION)
        if template_version != HEAT_TEMPLATE_VERSION:
            err_msg = ("Currently only heat_template_version %s "
                       "is supported." % HEAT_TEMPLATE_VERSION)
            raise HeatStackError(err_msg)
        current = self.current()
        self._template = helpers.merge_dicts(self._template, template)
        self._applied = self._template == current and self._applied

    @staticmethod
    def _remove_system_params(parameters):
        return dict((k, v) for k, v in parameters.items() if
                    not k.startswith('OS::'))

    def _get_status(self):
        status = [None]

        def status_func(state_value):
            status[0] = state_value
            return True
        self._wait_state(status_func)
        return status[0]

    def _wait_state(self, status_func, wait_progress=False):
        tries = 4
        delay = 1
        while tries > 0:
            while True:
                try:
                    stack_info = self._client.stacks.get(
                        stack_id=self._name)
                    status = stack_info.stack_status
                    tries = 4
                    delay = 1
                except heat_exc.HTTPNotFound:
                    stack_info = None
                    status = 'NOT_FOUND'
                except Exception:
                    tries -= 1
                    delay *= 2
                    if not tries:
                        raise
                    eventlet.sleep(delay)
                    break

                if 'IN_PROGRESS' in status:
                    eventlet.sleep(2)
                    continue

                last_stack_timestamps = self._last_stack_timestamps
                self._last_stack_timestamps = (None, None) if not stack_info \
                    else(stack_info.creation_time, stack_info.updated_time)

                if (wait_progress and last_stack_timestamps ==
                        self._last_stack_timestamps and
                        last_stack_timestamps != (None, None)):
                    eventlet.sleep(2)
                    continue

                if not status_func(status):
                    reason = ': {0}'.format(
                        stack_info.stack_status_reason) if stack_info else ''
                    raise EnvironmentError(
                        "Unexpected stack state {0}{1}".format(status, reason))

                try:
                    return dict([(t['output_key'], t['output_value'])
                                 for t in stack_info.outputs])
                except Exception:
                    return {}
        return {}

    def output(self):
        self._wait_push_thread()
        return self._wait_state(lambda status: True)

    def _push(self, object_store=None):
        template = copy.deepcopy(self._template)
        s_template = token_sanitizer.TokenSanitizer().sanitize(template)
        LOG.debug('Pushing: {template}'.format(
            template=json.dumps(s_template)))
        object_store = object_store or helpers.get_object_store()
        while True:
            try:
                with helpers.with_object_store(object_store):
                    current_status = self._get_status()
                    resources = template.get('Resources') or template.get(
                        'resources')
                    if current_status == 'NOT_FOUND':
                        if resources is not None:
                            token_client = self._get_token_client()
                            token_client.stacks.create(
                                stack_name=self._name,
                                parameters=self._parameters,
                                template=template,
                                files=self._files,
                                environment=self._hot_environment,
                                disable_rollback=True,
                                tags=self._tags)

                            self._wait_state(
                                lambda status: status == 'CREATE_COMPLETE')
                    else:
                        if resources is not None:
                            self._client.stacks.update(
                                stack_id=self._name,
                                parameters=self._parameters,
                                files=self._files,
                                environment=self._hot_environment,
                                template=template,
                                disable_rollback=True,
                                tags=self._tags)
                            self._wait_state(
                                lambda status: status == 'UPDATE_COMPLETE',
                                True)
                        else:
                            self.delete()
            except heat_exc.HTTPConflict as e:
                LOG.warning('Conflicting operation: {msg}'.format(msg=e))
                eventlet.sleep(3)
            else:
                break

        self._applied = self._template == template

    def push(self, is_async=False):
        if self._applied or self._template is None:
            return

        self._tags = ','.join(CONF.heat.stack_tags)
        if 'heat_template_version' not in self._template:
            self._template['heat_template_version'] = HEAT_TEMPLATE_VERSION

        if 'description' not in self._template and self._description:
            self._template['description'] = self._description

        self._kill_push_thread()
        if is_async:
            if self._push_thread is None:

                def cleanup():
                    try:
                        self._wait_push_thread()
                    finally:
                        self._push_thread = None

                dsl.get_execution_session().on_session_finish(cleanup)

            self._push_thread =\
                eventlet.greenthread.spawn_after(
                    1, self._push, helpers.get_object_store())
        else:
            self._push()

    def delete(self):
        self._kill_push_thread()
        while True:
            try:
                if not self.current():
                    return
                self._wait_state(lambda s: True)
                self._client.stacks.delete(stack_id=self._name)
                self._wait_state(
                    lambda status: status in ('DELETE_COMPLETE', 'NOT_FOUND'),
                    wait_progress=True)
            except heat_exc.NotFound:
                LOG.warning('Stack {stack_name} already deleted?'
                            .format(stack_name=self._name))
                break
            except heat_exc.HTTPConflict as e:
                LOG.warning('Conflicting operation: {msg}'.format(msg=e))
                eventlet.sleep(3)
            else:
                break

        self._template = {}
        self._applied = True
