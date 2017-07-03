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

from datetime import datetime
import mock

from murano.common import server
from murano.services import states
from murano.tests.unit import base
from murano.tests.unit import utils as test_utils


class ServerTest(base.MuranoTestCase):

    @classmethod
    def setUpClass(cls):
        super(ServerTest, cls).setUpClass()
        cls.result_endpoint = server.ResultEndpoint()
        cls.dummy_context = test_utils.dummy_context()

    @mock.patch('murano.common.server.status_reporter.get_notifier')
    @mock.patch('murano.common.server.LOG')
    @mock.patch('murano.common.server.get_last_deployment')
    @mock.patch('murano.common.server.models')
    @mock.patch('murano.common.server.session')
    def test_process_result(self, mock_db_session, mock_models,
                            mock_last_deployment, mock_log, mock_notifier):
        test_result = {
            'model': {
                'Objects': {
                    'applications': ['app1', 'app2'],
                    'services': ['service1', 'service2']
                }
            },
            'action': {
                'isException': False
            }
        }
        mock_env = mock.MagicMock(id='test_env_id',
                                  tenant_id='test_tenant_id',
                                  description=None,
                                  version=1)
        mock_db_session.get_session().query().get.return_value = mock_env
        mock_db_session.get_session().query().filter_by().count.\
            return_value = 0

        self.result_endpoint.process_result(self.dummy_context, test_result,
                                            'test_env_id')

        self.assertEqual(mock_env.description, test_result['model'])
        self.assertEqual(2, mock_env.version)
        self.assertEqual(test_result['action'],
                         mock_last_deployment().result)
        self.assertEqual('Deployment finished',
                         mock_models.Status().text)
        self.assertEqual('info', mock_models.Status().level)
        mock_last_deployment().statuses.append.assert_called_once_with(
            mock_models.Status())
        mock_db_session.get_session().query().filter_by.assert_any_call(
            **{'environment_id': mock_env.id,
               'state': states.SessionState.DEPLOYING})
        self.assertEqual(
            states.SessionState.DEPLOYED,
            mock_db_session.get_session().query().filter_by().first().state)
        mock_log.info.assert_called_once_with(
            'EnvId: {env_id} TenantId: {tenant_id} Status: '
            'Successful Apps: {services}'
            .format(env_id=mock_env.id,
                    tenant_id=mock_env.tenant_id,
                    services=test_result['model']['Objects']['services']))
        mock_notifier.return_value.report.assert_called_once_with(
            'environment.deploy.end',
            mock_db_session.get_session().query().get(mock_env.id).to_dict())

    @mock.patch('murano.common.server.LOG')
    @mock.patch('murano.common.server.get_last_deployment')
    @mock.patch('murano.common.server.models')
    @mock.patch('murano.common.server.session')
    def test_process_result_with_errors(self, mock_db_session, mock_models,
                                        mock_last_deployment, mock_log):
        test_result = {
            'model': {
                'Objects': {
                    'applications': ['app1', 'app2'],
                    'services': ['service1', 'service2']
                }
            },
            'action': {
                'isException': True
            }
        }
        mock_env = mock.MagicMock(id='test_env_id',
                                  tenant_id='test_tenant_id',
                                  description=None,
                                  version=1)
        mock_db_session.get_session().query().get.return_value = mock_env
        mock_db_session.get_session().query().filter_by().count.\
            return_value = 1

        self.result_endpoint.process_result(self.dummy_context, test_result,
                                            'test_env_id')

        self.assertEqual(mock_env.description, test_result['model'])
        self.assertEqual(test_result['action'],
                         mock_last_deployment().result)
        self.assertEqual('Deployment finished with errors',
                         mock_models.Status().text)
        mock_last_deployment().statuses.append.assert_called_once_with(
            mock_models.Status())
        mock_db_session.get_session().query().filter_by.assert_any_call(
            **{'environment_id': mock_env.id,
               'state': states.SessionState.DEPLOYING})
        self.assertEqual(
            states.SessionState.DEPLOY_FAILURE,
            mock_db_session.get_session().query().filter_by().first().state)
        mock_log.warning.assert_called_once_with(
            'EnvId: {env_id} TenantId: {tenant_id} Status: '
            'Failed Apps: {services}'
            .format(env_id=mock_env.id,
                    tenant_id=mock_env.tenant_id,
                    services=test_result['model']['Objects']['services']))

    @mock.patch('murano.common.server.LOG')
    @mock.patch('murano.common.server.get_last_deployment')
    @mock.patch('murano.common.server.models')
    @mock.patch('murano.common.server.session')
    def test_process_result_with_warnings(self, mock_db_session, mock_models,
                                          mock_last_deployment, mock_log):
        test_result = {
            'model': {
                'Objects': None,
                'ObjectsCopy': ['object1', 'object2']
            },
            'action': {
                'isException': True
            }
        }
        mock_env = mock.MagicMock(id='test_env_id',
                                  tenant_id='test_tenant_id',
                                  description=None,
                                  version=1)
        mock_db_session.get_session().query().get.return_value = mock_env
        # num_errors will be initialized to 0, num_warnings to 1
        mock_db_session.get_session().query().filter_by().count.\
            side_effect = [0, 1]

        self.result_endpoint.process_result(self.dummy_context, test_result,
                                            'test_env_id')

        self.assertEqual(mock_env.description, test_result['model'])
        self.assertEqual(test_result['action'],
                         mock_last_deployment().result)
        self.assertEqual('Deletion finished with warnings',
                         mock_models.Status().text)
        mock_last_deployment().statuses.append.assert_called_once_with(
            mock_models.Status())
        mock_db_session.get_session().query().filter_by.assert_any_call(
            **{'environment_id': mock_env.id,
               'state': states.SessionState.DELETING})
        self.assertEqual(
            states.SessionState.DELETE_FAILURE,
            mock_db_session.get_session().query().filter_by().first().state)
        mock_log.warning.assert_called_once_with(
            'EnvId: {env_id} TenantId: {tenant_id} Status: '
            'Failed Apps: {services}'
            .format(env_id=mock_env.id,
                    tenant_id=mock_env.tenant_id,
                    services=[]))

    @mock.patch('murano.common.server.LOG')
    @mock.patch('murano.common.server.session')
    def test_process_result_with_no_environment(self, mock_db_session,
                                                mock_log):
        test_result = {'model': None}
        mock_db_session.get_session().query().get.return_value = None

        result = self.result_endpoint.process_result(self.dummy_context,
                                                     test_result,
                                                     'test_env_id')
        self.assertIsNone(result)
        mock_log.warning.assert_called_once_with(
            'Environment result could not be handled, '
            'specified environment not found in database')

    @mock.patch('murano.common.server.environments')
    @mock.patch('murano.common.server.session')
    def test_process_result_with_no_objects(self, mock_db_session,
                                            mock_environments):
        test_result = {'model': {'Objects': None, 'ObjectsCopy': None}}

        result = self.result_endpoint.process_result(self.dummy_context,
                                                     test_result,
                                                     'test_env_id')
        self.assertIsNone(result)
        mock_environments.EnvironmentServices.remove.assert_called_once_with(
            'test_env_id')

    @mock.patch('murano.common.server.instances')
    def test_track_instance(self, mock_instances):
        test_payload = {
            'instance': 'test_instance',
            'instance_type': 'test_instance_type',
            'environment': 'test_environment',
            'unit_count': 'test_unit_count',
            'type_name': 'test_type_name',
            'type_title': 'test_type_title'
        }
        server.track_instance(test_payload)
        mock_instances.InstanceStatsServices.track_instance.\
            assert_called_once_with(test_payload['instance'],
                                    test_payload['environment'],
                                    test_payload['instance_type'],
                                    test_payload['type_name'],
                                    test_payload['type_title'],
                                    test_payload['unit_count'])

    @mock.patch('murano.common.server.instances')
    def test_untrack_instance(self, mock_instances):
        test_payload = {
            'instance': 'test_instance',
            'environment': 'test_environment'
        }
        server.untrack_instance(test_payload)
        mock_instances.InstanceStatsServices.destroy_instance.\
            assert_called_once_with(test_payload['instance'],
                                    test_payload['environment'])

    @mock.patch('murano.common.server.get_last_deployment')
    @mock.patch('murano.common.server.session')
    @mock.patch('murano.common.server.models')
    def test_report_notification(self, mock_models, mock_db_session,
                                 mock_last_deployment):
        mock_last_deployment.return_value = mock.MagicMock(
            id='test_deployment_id')

        test_report = {
            'id': 'test_report_id',
            'timestamp': datetime.now().isoformat(),
            'created': None
        }

        server.report_notification(test_report)
        self.assertIsNotNone(test_report['created'])
        mock_models.Status().update.assert_called_once_with(test_report)
        self.assertEqual('test_deployment_id', mock_models.Status().task_id)
        mock_db_session.get_session().add.assert_called_once_with(
            mock_models.Status())

    def test_get_last_deployment(self):
        mock_unit = mock.MagicMock()
        result = server.get_last_deployment(mock_unit, 'test_env_id')
        self.assertEqual(mock_unit.query().filter_by().order_by().first(),
                         result)
        mock_unit.query().filter_by.assert_any_call(
            environment_id='test_env_id')

    def test_service_class(self):
        service = server.Service()
        self.assertIsNone(service.server)

        # Test stop server.
        service.server = mock.MagicMock()
        service.stop(graceful=True)
        service.server.stop.assert_called_once_with()
        service.server.wait.assert_called_once_with()

        # Test reset server.
        service.reset()
        service.server.reset.assert_called_once_with()

    @mock.patch('murano.common.server.messaging')
    def test_notification_service_class(self, mock_messaging):
        mock_server = mock.MagicMock()
        mock_messaging.get_notification_listener.return_value = mock_server
        notification_service = server.NotificationService()
        self.assertIsNone(notification_service.server)

        notification_service.start()
        self.assertEqual(1,
                         mock_messaging.get_notification_listener.call_count)
        mock_server.start.assert_called_once_with()

    @mock.patch('murano.common.server.messaging')
    def test_api_service_class(self, mock_messaging):
        mock_server = mock.MagicMock()
        mock_messaging.get_rpc_server.return_value = mock_server
        api_service = server.ApiService()

        api_service.start()
        self.assertEqual(1,
                         mock_messaging.get_rpc_server.call_count)
        mock_server.start.assert_called_once_with()
