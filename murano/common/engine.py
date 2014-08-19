# Copyright (c) 2014 Mirantis Inc.
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

import uuid

import anyjson
import eventlet.debug
from oslo import messaging
from oslo.messaging import target

from murano.common import config
from murano.common.helpers import token_sanitizer
from murano.common import rpc
from murano.dsl import dsl_exception
from murano.dsl import executor
from murano.dsl import results_serializer
from murano.engine import environment
from murano.engine import package_class_loader
from murano.engine import package_loader
from murano.engine.system import status_reporter
import murano.engine.system.system_objects as system_objects
from murano.openstack.common.gettextutils import _  # noqa
from murano.openstack.common import log as logging

RPC_SERVICE = None

LOG = logging.getLogger(__name__)

eventlet.debug.hub_exceptions(False)


class TaskProcessingEndpoint(object):
    @staticmethod
    def handle_task(context, task):
        s_task = token_sanitizer.TokenSanitizer().sanitize(task)
        LOG.info(_('Starting processing task: {task_desc}').format(
            task_desc=anyjson.dumps(s_task)))

        result = task['model']
        try:
            task_executor = TaskExecutor(task)
            result = task_executor.execute()
        except Exception as e:
            LOG.exception('Error during task execution for tenant %s',
                          task['tenant_id'])
            msg_env = Environment(task['id'])
            reporter = status_reporter.StatusReporter()
            reporter.initialize(msg_env)
            reporter.report_error(msg_env, str(e))
        finally:
            rpc.api().process_result(result, task['id'])


def _prepare_rpc_service(server_id):
    endpoints = [TaskProcessingEndpoint()]

    transport = messaging.get_transport(config.CONF)
    s_target = target.Target('murano', 'tasks', server=server_id)
    return messaging.get_rpc_server(transport, s_target, endpoints, 'eventlet')


def get_rpc_service():
    global RPC_SERVICE

    if RPC_SERVICE is None:
        RPC_SERVICE = _prepare_rpc_service(str(uuid.uuid4()))
    return RPC_SERVICE


class Environment:
    def __init__(self, object_id):
        self.object_id = object_id


class TaskExecutor(object):
    @property
    def action(self):
        return self._action

    @property
    def environment(self):
        return self._environment

    @property
    def model(self):
        return self._model

    def __init__(self, task):
        self._action = task.get('action')
        self._model = task['model']
        self._environment = environment.Environment()
        self._environment.token = task['token']
        self._environment.tenant_id = task['tenant_id']

    def execute(self):
        token, tenant_id = self.environment.token, self.environment.tenant_id
        with package_loader.ApiPackageLoader(token, tenant_id) as pkg_loader:
            class_loader = package_class_loader.PackageClassLoader(pkg_loader)
            system_objects.register(class_loader, pkg_loader)

            exc = executor.MuranoDslExecutor(class_loader, self.environment)
            obj = exc.load(self.model)

            try:
                # Skip execution of action in case of no action is provided.
                # Model will be just loaded, cleaned-up and unloaded.
                # Most of the time this is used for deletion of environments.
                if self.action:
                    self._invoke(exc)
            except Exception as e:
                if isinstance(e, dsl_exception.MuranoPlException):
                    LOG.error('\n' + e.format(prefix='  '))
                else:
                    LOG.exception(e)
                reporter = status_reporter.StatusReporter()
                reporter.initialize(obj)
                reporter.report_error(obj, str(e))

            return results_serializer.serialize(obj, exc)

    def _invoke(self, mpl_executor):
        obj = mpl_executor.object_store.get(self.action['object_id'])
        method_name, args = self.action['method'], self.action['args']

        if obj is not None:
            obj.type.invoke(method_name, mpl_executor, obj, args)
