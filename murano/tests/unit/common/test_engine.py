# Copyright 2016 AT&T Corp
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from oslo_service import service

from murano.common import engine
from murano.dsl import constants
from murano.dsl import helpers
from murano.dsl import murano_package
from murano.engine import mock_context_manager
from murano.engine import package_loader
from murano.tests.unit import base


class TestEngineService(base.MuranoTestCase):
    def setUp(self):
        super(TestEngineService, self).setUp()
        self.engine = engine.EngineService()
        self.addCleanup(mock.patch.stopall)

    @mock.patch.object(service.Service, 'reset')
    @mock.patch.object(service.Service, 'stop')
    @mock.patch.object(service.Service, 'start')
    @mock.patch('murano.common.engine.messaging')
    def test_start_stop_reset(self, mock_messaging, mock_start,
                              mock_stop, mock_reset):
        self.engine.start()
        self.assertTrue(mock_messaging.get_rpc_transport.called)
        self.assertTrue(mock_messaging.get_rpc_server.called)
        self.assertTrue(mock_start.called)
        self.engine.stop()
        self.assertTrue(mock_stop.called)
        self.engine.reset()
        self.assertTrue(mock_reset.called)

    @mock.patch.object(service.Service, 'stop')
    @mock.patch.object(service.Service, 'start')
    @mock.patch('murano.common.engine.messaging')
    def test_stop_graceful(self, mock_messaging, mock_start, mock_stop):
        self.engine.start()
        self.assertTrue(mock_messaging.get_rpc_transport.called)
        self.assertTrue(mock_messaging.get_rpc_server.called)
        self.assertTrue(mock_start.called)
        self.engine.stop(graceful=True)
        self.assertTrue(mock_stop.called)


class TestTaskExecutor(base.MuranoTestCase):
    def setUp(self):
        super(TestTaskExecutor, self).setUp()
        self.task = {
            'action': {
                'args': None,
                'object_id': 'my_obj_id',
                'method': 'my_method'
            },
            'model': {
                'SystemData': {
                    'Packages': 'my_packages'
                },
                'project_id': 'my_tenant_id',
                'user_id': 'my_user_id'
            },
            'token': 'my_token',
            'project_id': 'my_tenant_id',
            'user_id': 'my_user_id',
            'id': 'my_env_id'
        }
        self.task_executor = engine.TaskExecutor(self.task)
        self.task_executor._model = self.task['model']
        self.task_executor._session.token = self.task['token']
        self.task_executor._session.project_id = self.task['project_id']
        self.task_executor._session.user_id = self.task['user_id']
        self.task_executor._session.environment_owner_project_id_ = \
            self.task['model']['project_id']
        self.task_executor._session.environment_owner_user_id = \
            self.task['model']['user_id']
        (self.task_executor._session
            .system_attributes) = (self.task_executor._model.
                                   get('SystemData', {}))
        self.addCleanup(mock.patch.stopall)

    def test_properties(self):
        self.assertEqual(self.task['action'], self.task_executor.action)
        self.assertEqual(self.task_executor._session,
                         self.task_executor.session)
        self.assertEqual(self.task['model'], self.task_executor.model)

    @mock.patch('murano.common.engine.auth_utils.delete_trust')
    @mock.patch('murano.common.engine.auth_utils.create_trust')
    @mock.patch('murano.common.engine.package_loader.'
                'CombinedPackageLoader.import_fixation_table')
    @mock.patch('murano.common.engine.TaskExecutor._execute')
    def test_execute(self, mock_execute, mock_loader,
                     mock_create, mock_delete):
        mock_loader.return_value = {'SystemData': 'my_sys_data'}
        mock_create.return_value = 'trust_id'
        expected = {
            'action': {
                'result': '?',
                'isException': False
            }
        }
        mock_execute.return_value = expected
        result = self.task_executor.execute()

        self.assertEqual(expected, result)
        self.assertTrue(mock_execute.called)
        self.assertTrue(mock_loader.called)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_delete.called)

    def test_private_execute(self):
        mock_loader = mock.Mock()
        result = self.task_executor._execute(mock_loader)
        expected = {
            'action': {
                'result': None,
                'isException': False
            }
        }
        self.assertEqual(expected, result)

    @mock.patch('murano.common.engine.auth_utils.delete_trust')
    @mock.patch('murano.common.engine.auth_utils.create_trust')
    def test_trust(self, mock_create, mock_delete):
        mock_create.return_value = 'trust_id'
        self.task_executor._create_trust()
        self.assertEqual('trust_id', self.task_executor._session.trust_id)
        self.assertTrue(mock_create.called)

        self.task_executor._delete_trust()
        self.assertIsNone(self.task_executor._session.trust_id)
        self.assertTrue(mock_delete.called)


class TestStaticActionExecutor(base.MuranoTestCase):

    def setUp(self):
        super(TestStaticActionExecutor, self).setUp()

        self.action = {
            'method': 'TestAction',
            'args': {'name': 'foo'},
            'class_name': 'TestClass',
            'pkg_name': 'TestPackage',
            'class_version': '=0'
        }
        self.task = {
            'action': self.action,
            'token': 'test_token',
            'project_id': 'test_tenant',
            'user_id': 'test_user',
            'id': 'test_task_id'
        }
        self.task_executor = engine.StaticActionExecutor(self.task)
        self.assertIsInstance(self.task_executor._reporter,
                              engine.status_reporter.StatusReporter)
        self.assertEqual(self.task['id'],
                         self.task_executor._reporter._environment_id)

    def test_action_property(self):
        self.assertEqual(self.action, self.task_executor.action)

    def test_session_property(self):
        self.assertIsInstance(self.task_executor.session,
                              engine.execution_session.ExecutionSession)
        self.assertEqual('test_token', self.task_executor.session.token)
        self.assertEqual('test_tenant', self.task_executor.session.project_id)
        self.assertIsInstance(self.task_executor._model_policy_enforcer,
                              engine.enforcer.ModelPolicyEnforcer)
        self.assertEqual(
            self.task_executor.session,
            self.task_executor._model_policy_enforcer._execution_session)

    @mock.patch.object(engine, 'serializer')
    @mock.patch.object(engine.dsl_executor.MuranoDslExecutor, 'package_loader')
    def test_execute(self, mock_package_loader, mock_serializer):
        mock_class = mock.Mock()
        mock_package = mock.Mock(spec=murano_package.MuranoPackage)
        mock_package.find_class.return_value = mock_class
        mock_package_loader.load_package.return_value = mock_package
        version_spec = helpers.parse_version_spec(self.action['class_version'])

        self.task_executor.execute()
        mock_package_loader.load_package.assert_called_once_with(
            'TestPackage', version_spec)
        mock_package.find_class.assert_called_once_with(
            self.action['class_name'], search_requirements=False)
        mock_class.invoke.assert_called_once_with('TestAction', None, (),
                                                  {'name': 'foo'})
        self.assertTrue(mock_serializer.serialize.called)

    @mock.patch.object(engine, 'serializer')
    @mock.patch.object(engine.dsl_executor.MuranoDslExecutor, 'package_loader')
    def test_execute_without_package_name(self, mock_package_loader,
                                          mock_serializer):
        mock_class = mock.Mock()
        mock_package = mock.Mock(spec=murano_package.MuranoPackage)
        mock_package.find_class.return_value = mock_class
        mock_package_loader.load_class_package.return_value = mock_package
        version_spec = helpers.parse_version_spec(self.action['class_version'])
        self.task_executor.action['pkg_name'] = None

        self.task_executor.execute()
        mock_package_loader.load_class_package.assert_called_once_with(
            'TestClass', version_spec)
        mock_package.find_class.assert_called_once_with(
            self.action['class_name'], search_requirements=False)
        mock_class.invoke.assert_called_once_with('TestAction', None, (),
                                                  {'name': 'foo'})
        self.assertTrue(mock_serializer.serialize.called)


class TestSchemaEndpoint(base.MuranoTestCase):

    def setUp(self):
        super(TestSchemaEndpoint, self).setUp()
        context_manager = mock_context_manager.MockContextManager()
        self.context = context_manager.create_root_context(
            constants.RUNTIME_VERSION_1_5)

    @mock.patch('murano.common.engine.schema_generator')
    @mock.patch('murano.common.engine.package_loader')
    def test_generate_schema(self, mock_package_loader,
                             mock_schema_generator):
        mock_pkg_loader = mock.Mock(
            spec=package_loader.CombinedPackageLoader)
        mock_package_loader.CombinedPackageLoader().__enter__.return_value =\
            mock_pkg_loader
        mock_schema_generator.generate_schema.return_value = 'test_schema'

        arg1, arg2, arg3 = mock.Mock(), mock.Mock(), mock.Mock()
        test_args = (arg1, arg2, arg3)
        test_kwargs = {'foo': 'bar', 'class_name': 'test_class_name'}

        result = engine.SchemaEndpoint.generate_schema(
            self.context, *test_args, **test_kwargs)

        self.assertEqual('test_schema', result)
        mock_schema_generator.generate_schema.assert_called_once_with(
            mock_pkg_loader, mock.ANY, *test_args, **test_kwargs)


class TestTaskProcessingEndpoint(base.MuranoTestCase):

    def setUp(self):
        super(TestTaskProcessingEndpoint, self).setUp()

        self.action = {
            'method': 'TestAction',
            'args': {'name': 'foo'},
            'class_name': 'TestClass',
            'pkg_name': 'TestPackage',
            'class_version': '=0',
            'object_id': 'test_object_id'
        }
        self.task = {
            'action': self.action,
            'model': {
                'SystemData': {'TrustId': 'test_trust_id'},
                'project_id': 'test_tenant',
                'user_id': 'test_user'
            },
            'token': 'test_token',
            'project_id': 'test_tenant',
            'user_id': 'test_user',
            'id': 'test_task_id'
        }
        context_manager = mock_context_manager.MockContextManager()
        self.context = context_manager.create_root_context(
            constants.RUNTIME_VERSION_1_5)

    @mock.patch.object(engine.TaskExecutor, '_delete_trust')
    @mock.patch.object(engine, 'rpc')
    @mock.patch.object(engine.dsl_executor.MuranoDslExecutor, 'finalize')
    @mock.patch.object(engine, 'LOG')
    def test_handle_task(self, mock_log, mock_finalize, mock_rpc,
                         mock_delete_trust):
        mock_finalize.return_value = self.task['model']

        handle_task = engine.TaskProcessingEndpoint.handle_task
        handle_task(self.context, self.task)

        mock_delete_trust.assert_called_once_with()
        mock_rpc.api().process_result.assert_called_once_with(
            mock.ANY, 'test_task_id')
        self.assertEqual(2, mock_log.info.call_count)
        self.assertIn('Starting processing task:',
                      str(mock_log.info.mock_calls[0]))
        self.assertIn('Finished processing task:',
                      str(mock_log.info.mock_calls[1]))


class TestStaticActionEndpoint(base.MuranoTestCase):

    def setUp(self):
        super(TestStaticActionEndpoint, self).setUp()

        self.action = {
            'method': 'TestAction',
            'args': {'name': 'foo'},
            'class_name': 'TestClass',
            'pkg_name': 'TestPackage',
            'class_version': '=0',
            'object_id': 'test_object_id'
        }
        self.task = {
            'action': self.action,
            'model': {'SystemData': {'TrustId': 'test_trust_id'}},
            'token': 'test_token',
            'project_id': 'test_tenant',
            'user_id': 'test_user',
            'id': 'test_task_id'
        }
        context_manager = mock_context_manager.MockContextManager()
        self.context = context_manager.create_root_context(
            constants.RUNTIME_VERSION_1_5)

    @mock.patch('murano.dsl.serializer.serialize')
    @mock.patch('murano.common.engine.package_loader')
    @mock.patch.object(engine, 'LOG')
    def test_call_static_action(self, mock_log, mock_package_loader,
                                mock_serialize):
        mock_pkg_loader = mock.Mock(
            spec=package_loader.CombinedPackageLoader)
        mock_package_loader.CombinedPackageLoader().__enter__.return_value =\
            mock_pkg_loader

        expected = {
            'Objects': ['foo'],
            'ObjectsCopy': ['bar'],
            'Attributes': ['baz']
        }
        mock_serialize.return_value = expected

        call_static_action = engine.StaticActionEndpoint.call_static_action
        result = call_static_action(self.context, self.task)

        self.assertEqual(expected, result)
        self.assertEqual(2, mock_log.info.call_count)
        self.assertIn('Starting execution of static action:',
                      str(mock_log.info.mock_calls[0]))
        self.assertIn('Finished execution of static action:',
                      str(mock_log.info.mock_calls[1]))
