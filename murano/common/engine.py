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

import traceback
import uuid

import eventlet.debug
from oslo import messaging
from oslo.messaging import target
from oslo.serialization import jsonutils

from murano.common import auth_utils
from murano.common import config
from murano.common.helpers import token_sanitizer
from murano.common import plugin_loader
from murano.common import rpc
from murano.dsl import dsl_exception
from murano.dsl import executor
from murano.dsl import serializer
from murano.engine import client_manager
from murano.engine import environment
from murano.engine import package_class_loader
from murano.engine import package_loader
from murano.engine.system import status_reporter
import murano.engine.system.system_objects as system_objects
from murano.common.i18n import _LI, _LE
from murano.openstack.common import log as logging
from murano.policy import model_policy_enforcer as enforcer


RPC_SERVICE = None
PLUGIN_LOADER = None

LOG = logging.getLogger(__name__)

eventlet.debug.hub_exceptions(False)


class TaskProcessingEndpoint(object):
    @staticmethod
    def handle_task(context, task):
        s_task = token_sanitizer.TokenSanitizer().sanitize(task)
        LOG.info(_LI('Starting processing task: {task_desc}').format(
            task_desc=jsonutils.dumps(s_task)))

        result = {'model': task['model']}
        try:
            task_executor = TaskExecutor(task)
            result = task_executor.execute()
        except Exception as e:
            LOG.exception(_LE('Error during task execution for tenant %s'),
                          task['tenant_id'])
            result['action'] = TaskExecutor.exception_result(
                e, traceback.format_exc())
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


def get_plugin_loader():
    global PLUGIN_LOADER

    if PLUGIN_LOADER is None:
        PLUGIN_LOADER = plugin_loader.PluginLoader()
    return PLUGIN_LOADER


class Environment(object):
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
        self._environment.system_attributes = self._model.get('SystemData', {})
        self._environment.clients = client_manager.ClientManager()

        self._model_policy_enforcer = enforcer.ModelPolicyEnforcer(
            self._environment)

    def execute(self):
        self._create_trust()

        try:
            # !!! please do not delete 2 commented lines of code below.
            # Uncomment to make engine load packages from
            # local folder rather than from API !!!

            # pkg_loader = package_loader.DirectoryPackageLoader('./meta')
            # return self._execute(pkg_loader)

            murano_client_factory = lambda: \
                self._environment.clients.get_murano_client(self._environment)
            with package_loader.ApiPackageLoader(
                    murano_client_factory,
                    self._environment.tenant_id) as pkg_loader:
                return self._execute(pkg_loader)
        finally:
            if self._model['Objects'] is None:
                self._delete_trust()

    def _execute(self, pkg_loader):
        class_loader = package_class_loader.PackageClassLoader(pkg_loader)
        system_objects.register(class_loader, pkg_loader)
        get_plugin_loader().register_in_loader(class_loader)

        exc = executor.MuranoDslExecutor(class_loader, self.environment)
        obj = exc.load(self.model)

        self._validate_model(obj, self.action, class_loader)
        action_result = None
        exception = None
        exception_traceback = None

        try:
            LOG.info(_LI('Invoking pre-cleanup hooks'))
            self.environment.start()
            exc.cleanup(self._model)
        except Exception as e:
            exception = e
            exception_traceback = TaskExecutor._log_exception(e, obj, '<GC>')
        finally:
            LOG.info(_LI('Invoking post-cleanup hooks'))
            self.environment.finish()

        if exception is None and self.action:
            try:
                LOG.info(_LI('Invoking pre-execution hooks'))
                self.environment.start()
                action_result = self._invoke(exc)
            except Exception as e:
                exception = e
                exception_traceback = TaskExecutor._log_exception(
                    e, obj, self.action['method'])
            finally:
                LOG.info(_LI('Invoking post-execution hooks'))
                self.environment.finish()

        model = serializer.serialize_model(obj, exc)
        model['SystemData'] = self._environment.system_attributes
        result = {
            'model': model,
            'action': {
                'result': None,
                'isException': False
            }
        }
        if exception is not None:
            result['action'] = TaskExecutor.exception_result(
                exception, exception_traceback)
            # NOTE(kzaitsev): Exception here means that it happened during
            # cleanup. ObjectsCopy and Attributes would be empty if obj
            # is empty. This would cause failed env to be deleted.
            # Therefore restore these attrs from self._model
            for attr in ['ObjectsCopy', 'Attributes']:
                if not model.get(attr):
                    model[attr] = self._model[attr]
        else:
            result['action']['result'] = serializer.serialize_object(
                action_result)

        return result

    @staticmethod
    def _log_exception(e, root, method_name):
        if isinstance(e, dsl_exception.MuranoPlException):
            LOG.error('\n' + e.format(prefix='  '))
            exception_traceback = e.format()
        else:
            exception_traceback = traceback.format_exc()
            LOG.exception(
                _LE("Exception %(exc)s occurred"
                    " during invocation of %(method)s"),
                {'exc': e, 'method': method_name})
        if root is not None:
            reporter = status_reporter.StatusReporter()
            reporter.initialize(root)
            reporter.report_error(root, str(e))
        return exception_traceback

    @staticmethod
    def exception_result(exception, exception_traceback):
        return {
            'isException': True,
            'result': {
                'message': str(exception),
                'details': exception_traceback
            }
        }

    def _validate_model(self, obj, action, class_loader):
        if config.CONF.engine.enable_model_policy_enforcer:
            if obj is not None:
                if action is not None and action['method'] == 'deploy':
                    self._model_policy_enforcer.validate(obj.to_dictionary(),
                                                         class_loader)

    def _invoke(self, mpl_executor):
        obj = mpl_executor.object_store.get(self.action['object_id'])
        method_name, args = self.action['method'], self.action['args']

        if obj is not None:
            return obj.type.invoke(method_name, mpl_executor, obj, args)

    def _create_trust(self):
        if not config.CONF.engine.use_trusts:
            return
        trust_id = self._environment.system_attributes.get('TrustId')
        if not trust_id:
            trust_id = auth_utils.create_trust(self._environment.token,
                                               self._environment.tenant_id)
            self._environment.system_attributes['TrustId'] = trust_id
        self._environment.trust_id = trust_id

    def _delete_trust(self):
        trust_id = self._environment.trust_id
        if trust_id:
            auth_utils.delete_trust(self._environment.trust_id)
            self._environment.system_attributes['TrustId'] = None
            self._environment.trust_id = None
