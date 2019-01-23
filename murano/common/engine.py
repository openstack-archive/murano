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

import copy
import traceback
import uuid

import eventlet.debug
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher
from oslo_messaging import target
from oslo_serialization import jsonutils
from oslo_service import service

from murano.common import auth_utils
from murano.common.helpers import token_sanitizer
from murano.common.plugins import extensions_loader
from murano.common import rpc
from murano.dsl import context_manager
from murano.dsl import dsl_exception
from murano.dsl import executor as dsl_executor
from murano.dsl import helpers
from murano.dsl import schema_generator
from murano.dsl import serializer
from murano.engine import execution_session
from murano.engine import package_loader
from murano.engine.system import status_reporter
from murano.engine.system import yaql_functions
from murano.policy import model_policy_enforcer as enforcer

CONF = cfg.CONF

PLUGIN_LOADER = None

LOG = logging.getLogger(__name__)

eventlet.debug.hub_exceptions(False)


# noinspection PyAbstractClass
class EngineService(service.Service):
    def __init__(self):
        super(EngineService, self).__init__()
        self.server = None

    def start(self):
        endpoints = [
            TaskProcessingEndpoint(),
            StaticActionEndpoint(),
            SchemaEndpoint()
        ]

        transport = messaging.get_rpc_transport(CONF)
        s_target = target.Target('murano', 'tasks', server=str(uuid.uuid4()))
        access_policy = dispatcher.DefaultRPCAccessPolicy
        self.server = messaging.get_rpc_server(
            transport, s_target, endpoints, 'eventlet',
            access_policy=access_policy)
        self.server.start()
        super(EngineService, self).start()

    def stop(self, graceful=False):
        if self.server:
            self.server.stop()
            if graceful:
                self.server.wait()
        super(EngineService, self).stop()

    def reset(self):
        if self.server:
            self.server.reset()
        super(EngineService, self).reset()


def get_plugin_loader():
    global PLUGIN_LOADER

    if PLUGIN_LOADER is None:
        PLUGIN_LOADER = extensions_loader.PluginLoader()
    return PLUGIN_LOADER


class ContextManager(context_manager.ContextManager):
    def create_root_context(self, runtime_version):
        root_context = super(ContextManager, self).create_root_context(
            runtime_version)
        return helpers.link_contexts(
            root_context, yaql_functions.get_context(runtime_version))

    def create_package_context(self, package):
        context = super(ContextManager, self).create_package_context(
            package)
        if package.name == 'io.murano':
            context = helpers.link_contexts(
                context, yaql_functions.get_restricted_context())
        return context


class SchemaEndpoint(object):
    @classmethod
    def generate_schema(cls, context, *args, **kwargs):
        session = execution_session.ExecutionSession()
        session.token = context['token']
        session.project_id = context['project_id']
        with package_loader.CombinedPackageLoader(session) as pkg_loader:
            return schema_generator.generate_schema(
                pkg_loader, ContextManager(), *args, **kwargs)


class TaskProcessingEndpoint(object):
    @classmethod
    def handle_task(cls, context, task):
        result = cls.execute(task)
        rpc.api().process_result(result, task['id'])

    @staticmethod
    def execute(task):
        s_task = token_sanitizer.TokenSanitizer().sanitize(task)
        LOG.info('Starting processing task: {task_desc}'.format(
            task_desc=jsonutils.dumps(s_task)))

        result = None
        reporter = status_reporter.StatusReporter(task['id'])

        try:
            task_executor = TaskExecutor(task, reporter)
            result = task_executor.execute()
            return result
        finally:
            s_result = token_sanitizer.TokenSanitizer().sanitize(result)
            LOG.info('Finished processing task: {task_desc}'.format(
                task_desc=jsonutils.dumps(s_result)))


class StaticActionEndpoint(object):
    @classmethod
    def call_static_action(cls, context, task):
        s_task = token_sanitizer.TokenSanitizer().sanitize(task)
        LOG.info('Starting execution of static action: '
                 '{task_desc}'.format(task_desc=jsonutils.dumps(s_task)))

        result = None
        reporter = status_reporter.StatusReporter(task['id'])

        try:
            task_executor = StaticActionExecutor(task, reporter)
            result = task_executor.execute()
            return result
        finally:
            LOG.info('Finished execution of static action: '
                     '{task_desc}'.format(task_desc=jsonutils.dumps(result)))


class TaskExecutor(object):
    @property
    def action(self):
        return self._action

    @property
    def session(self):
        return self._session

    @property
    def model(self):
        return self._model

    def __init__(self, task, reporter=None):
        if reporter is None:
            reporter = status_reporter.StatusReporter(task['id'])
        self._action = task.get('action')
        self._model = task['model']
        self._session = execution_session.ExecutionSession()
        self._session.token = task['token']
        self._session.project_id = task['project_id']
        self._session.user_id = task['user_id']
        self._session.environment_owner_project_id = self._model['project_id']
        self._session.environment_owner_user_id = self._model['user_id']
        self._session.system_attributes = self._model.get('SystemData', {})
        self._reporter = reporter

        self._model_policy_enforcer = enforcer.ModelPolicyEnforcer(
            self._session)

    def execute(self):
        try:
            self._create_trust()
        except Exception as e:
            return self.exception_result(e, None, '<system>')

        with package_loader.CombinedPackageLoader(self._session) as pkg_loader:
            pkg_loader.import_fixation_table(
                self._session.system_attributes.get('Packages', {}))
            result = self._execute(pkg_loader)
            self._session.system_attributes[
                'Packages'] = pkg_loader.export_fixation_table()
        self._model['SystemData'] = self._session.system_attributes
        self._model['project_id'] = self._session.environment_owner_project_id
        self._model['user_id'] = self._session.environment_owner_user_id
        result['model'] = self._model

        if (not self._model.get('Objects') and
                not self._model.get('ObjectsCopy')):
            try:
                self._delete_trust()
            except Exception:
                LOG.warning('Cannot delete trust', exc_info=True)

        return result

    def _execute(self, pkg_loader):

        get_plugin_loader().register_in_loader(pkg_loader)
        with dsl_executor.MuranoDslExecutor(
                pkg_loader, ContextManager(), self.session) as executor:
            try:
                obj = executor.load(self.model)
            except Exception as e:
                return self.exception_result(e, None, '<load>')

            if obj is not None:
                try:
                    self._validate_model(obj.object, pkg_loader, executor)
                except Exception as e:
                    return self.exception_result(e, obj, '<validate>')
            try:
                LOG.debug('Invoking pre-cleanup hooks')
                self.session.start()
                executor.object_store.cleanup()
            except Exception as e:
                return self.exception_result(e, obj, '<GC>')
            finally:
                LOG.debug('Invoking post-cleanup hooks')
                self.session.finish()
            self._model['ObjectsCopy'] = \
                copy.deepcopy(self._model.get('Objects'))

            action_result = None
            if self.action:
                try:
                    LOG.debug('Invoking pre-execution hooks')
                    self.session.start()
                    action_result = self._invoke(executor)
                except Exception as e:
                    return self.exception_result(e, obj, self.action['method'])
                finally:
                    LOG.debug('Invoking post-execution hooks')
                    self.session.finish()
                    self._model = executor.finalize(obj)
            try:
                action_result = serializer.serialize(action_result, executor)
            except Exception as e:
                return self.exception_result(e, None, '<result>')

        pkg_loader.compact_fixation_table()
        return {
            'action': {
                'result': action_result,
                'isException': False
            }
        }

    def exception_result(self, exception, root, method_name):
        if isinstance(exception, dsl_exception.MuranoPlException):
            LOG.error('\n' + exception.format(prefix='  '))
            exception_traceback = exception.format()
        else:
            exception_traceback = traceback.format_exc()
            LOG.exception(
                ("Exception %(exc)s occurred"
                 " during invocation of %(method)s"),
                {'exc': exception, 'method': method_name})
        self._reporter.report_error(root, str(exception))

        return {
            'action': {
                'isException': True,
                'result': {
                    'message': str(exception),
                    'details': exception_traceback
                }
            }
        }

    def _validate_model(self, obj, pkg_loader, executor):
        if CONF.engine.enable_model_policy_enforcer:
            if obj is not None:
                with helpers.with_object_store(executor.object_store):
                    self._model_policy_enforcer.modify(obj, pkg_loader)
                    self._model_policy_enforcer.validate(obj.to_dictionary(),
                                                         pkg_loader)

    def _invoke(self, mpl_executor):
        obj = mpl_executor.object_store.get(self.action['object_id'])
        method_name, kwargs = self.action['method'], self.action['args']

        if obj is not None:
            return mpl_executor.run(obj.type, method_name, obj, (), kwargs)

    def _create_trust(self):
        if not CONF.engine.use_trusts:
            return
        trust_id = self._session.system_attributes.get('TrustId')
        if not trust_id:
            trust_id = auth_utils.create_trust(
                self._session.token, self._session.project_id)
            self._session.system_attributes['TrustId'] = trust_id
        self._session.trust_id = trust_id

    def _delete_trust(self):
        trust_id = self._session.trust_id
        if trust_id:
            auth_utils.delete_trust(self._session)
            self._session.system_attributes['TrustId'] = None
            self._session.trust_id = None


class StaticActionExecutor(object):
    @property
    def action(self):
        return self._action

    @property
    def session(self):
        return self._session

    def __init__(self, task, reporter=None):
        if reporter is None:
            reporter = status_reporter.StatusReporter(task['id'])
        self._action = task['action']
        self._session = execution_session.ExecutionSession()
        self._session.token = task['token']
        self._session.project_id = task['project_id']
        self._session.user_id = task['user_id']
        self._reporter = reporter
        self._model_policy_enforcer = enforcer.ModelPolicyEnforcer(
            self._session)

    def execute(self):
        with package_loader.CombinedPackageLoader(self._session) as pkg_loader:
            get_plugin_loader().register_in_loader(pkg_loader)
            executor = dsl_executor.MuranoDslExecutor(pkg_loader,
                                                      ContextManager())
            action_result = self._invoke(executor)
            action_result = serializer.serialize(action_result, executor)
            return action_result

    def _invoke(self, mpl_executor):
        class_name = self.action['class_name']
        pkg_name = self.action['pkg_name']
        class_version = self.action['class_version']
        version_spec = helpers.parse_version_spec(class_version)
        if pkg_name:
            package = mpl_executor.package_loader.load_package(
                pkg_name, version_spec)
        else:
            package = mpl_executor.package_loader.load_class_package(
                class_name, version_spec)
        cls = package.find_class(class_name, search_requirements=False)
        method_name, kwargs = self.action['method'], self.action['args']

        return mpl_executor.run(cls, method_name, None, (), kwargs)
