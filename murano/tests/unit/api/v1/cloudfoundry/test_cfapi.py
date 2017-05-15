#    Copyright (c) 2015 Mirantis, Inc.
#    Copyright 2017 AT&T Corporation
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

import json
import mock
from oslo_serialization import base64
from webob import response

from murano.cfapi import cfapi as api
from murano.common import wsgi
from murano.db import models
from murano.tests.unit import base

from muranoclient.common import exceptions


class TestController(base.MuranoTestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.controller = api.Controller()

        self.request = mock.MagicMock()
        auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        self.request.headers = {'Authorization': auth,
                                'X-Auth-Token': 'foo-bar',
                                'X-Project-Id': 'bar-baz'}
        self.addCleanup(mock.patch.stopall)

    @mock.patch('murano.common.policy.check_is_admin')
    @mock.patch('murano.cfapi.cfapi._get_muranoclient')
    def test_list(self, mock_client, mock_policy):

        pkg0 = mock.MagicMock()
        pkg0.id = 'xxx'
        pkg0.name = 'foo'
        pkg0.description = 'stub pkg'

        mock_client.return_value.packages.filter =\
            mock.MagicMock(return_value=[pkg0])

        answer = {'services': [{'bindable': True,
                                'description': pkg0.description,
                                'id': pkg0.id,
                                'name': pkg0.name,
                                'plans': [{'description': ('Default plan for '
                                                           'the service '
                                                           '{name}').format(
                                                               name=pkg0.name),
                                           'id': 'xxx-1',
                                           'name': 'default'}],
                                'tags': []}]}

        resp = self.controller.list(self.request)
        self.assertEqual(answer, resp)

    @mock.patch('murano.common.policy.check_is_admin')
    @mock.patch('murano.cfapi.cfapi._get_muranoclient')
    @mock.patch('murano.db.services.cf_connections.set_instance_for_service')
    @mock.patch('murano.db.services.cf_connections.get_environment_for_space')
    @mock.patch('murano.db.services.cf_connections.get_tenant_for_org')
    def test_provision_from_scratch(self, mock_get_tenant,
                                    mock_get_environment, mock_is, mock_client,
                                    mock_policy):

        body = {"space_guid": "s1-p1",
                "organization_guid": "o1-r1",
                "plan_id": "p1-l1",
                "service_id": "s1-e1",
                "parameters": {'some_parameter': 'value',
                               '?': {}}}
        self.request.body = json.dumps(body)

        mock_get_environment.return_value = '555-555'
        mock_client.return_value = mock.MagicMock()

        resp = self.controller.provision(self.request, {}, '111-111')

        self.assertIsInstance(resp, response.Response)

    @mock.patch('murano.common.policy.check_is_admin')
    @mock.patch('murano.cfapi.cfapi._get_muranoclient')
    @mock.patch('murano.db.services.cf_connections.set_instance_for_service')
    @mock.patch('murano.db.services.cf_connections.set_environment_for_space')
    @mock.patch('murano.db.services.cf_connections.set_tenant_for_org')
    @mock.patch('murano.db.services.cf_connections.get_environment_for_space')
    @mock.patch('murano.db.services.cf_connections.get_tenant_for_org')
    def test_provision_existent(self, mock_get_tenant,
                                mock_get_environment, mock_set_tenant,
                                mock_set_environment, mock_is, mock_client,
                                mock_policy):

        body = {"space_guid": "s1-p1",
                "organization_guid": "o1-r1",
                "plan_id": "p1-l1",
                "service_id": "s1-e1",
                "parameters": {'some_parameter': 'value',
                               '?': {}}}
        self.request.body = json.dumps(body)

        mock_package = mock_client.return_value.packages.get
        mock_package.return_value = mock.MagicMock()
        mock_get_environment.side_effect = AttributeError
        mock_get_tenant.side_effect = AttributeError

        resp = self.controller.provision(self.request, {}, '111-111')

        self.assertIsInstance(resp, response.Response)

    @mock.patch('murano.cfapi.cfapi._get_muranoclient')
    @mock.patch('murano.db.services.cf_connections.get_service_for_instance')
    def test_deprovision(self, mock_get_si, mock_client):
        service = mock.MagicMock()
        service.service_id = '111-111'
        service.tenant_id = '222-222'
        service.env_id = '333-333'
        mock_get_si.return_value = service

        resp = self.controller.deprovision(self.request, '555-555')

        self.assertIsInstance(resp, response.Response)

    @mock.patch('murano.cfapi.cfapi._get_muranoclient')
    @mock.patch('murano.db.services.cf_connections.get_service_for_instance')
    def test_bind(self, mock_get_si, mock_client):
        service = mock.MagicMock()
        service.service_id = '111-111'
        service.tenant_id = '222-222'
        service.env_id = '333-333'
        mock_get_si.return_value = service

        services = [{'id': 'xxx-xxx-xxx',
                     '?': {'id': '111-111',
                           '_actions': {
                               'dafsa_getCredentials': {
                                   'name': 'getCredentials'}}},
                     'instance': {}}]
        mock_client.return_value.environments.get =\
            mock.MagicMock(return_value=mock.MagicMock(services=services))

        mock_client.return_value.actions.get_result =\
            mock.MagicMock(return_value={'result': {'smthg': 'nothing'}})
        nice_resp = {'credentials': {'smthg': 'nothing'}}
        resp = self.controller.bind(self.request, {}, '555-555', '666-666')

        self.assertEqual(nice_resp, resp)

    def test_package_to_service(self):
        mock_package = mock.Mock(
            spec_set=models.Package, id='foo_package_id',
            description='a'*257, tags=[mock.sentinel.package_tag])
        mock_package.configure_mock(name=mock.sentinel.package_name)

        expected_service = {
            'id': 'foo_package_id',
            'name': mock.sentinel.package_name,
            'description': 'a'*253 + ' ...',
            'bindable': True,
            'tags': [mock.sentinel.package_tag],
            'plans': [{
                'id': 'foo_package_id-1',
                'name': 'default',
                'description':
                'Default plan for the service sentinel.package_name'
            }]
        }
        service = self.controller._package_to_service(mock_package)

        for key, val in expected_service.items():
            if key != 'plans':
                self.assertEqual(val, service[key])
            else:
                self.assertEqual(1, len(service['plans']))
                for plan_key, plan_val in expected_service['plans'][0].items():
                    self.assertEqual(plan_val, service['plans'][0][plan_key])

    def test_get_service_return_none(self):
        mock_env = mock.Mock(services=[])
        self.assertIsNone(self.controller._get_service(mock_env, None))

    @mock.patch.object(api, 'LOG', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    def test_provision_except_http_not_found(self, mock_get_muranoclient,
                                             mock_db_cf, mock_log):
        test_body = {
            'space_guid': 'foo_space_guid',
            'organization_guid': 'foo_organization_guid',
            'plan_id': 'foo_plan_id',
            'service_id': 'foo_service_id',
            'parameters': {}
        }
        test_headers = {
            'X-Auth-Token': mock.sentinel.token
        }
        mock_request = mock.Mock(body=json.dumps(test_body),
                                 headers=test_headers)
        mock_muranoclient = mock.Mock()
        mock_muranoclient.environments.get.side_effect = \
            exceptions.HTTPNotFound
        mock_muranoclient.environments.create.return_value = \
            mock.Mock(id=mock.sentinel.alt_environment_id)
        mock_get_muranoclient.return_value = mock_muranoclient
        mock_db_cf.get_environment_for_space.return_value = \
            mock.sentinel.environment_id

        resp = self.controller.provision(mock_request, None, None)

        self.assertEqual(202, resp.status_code)
        self.assertEqual({}, resp.json_body)
        mock_db_cf.get_environment_for_space.assert_called_once_with(
            'foo_space_guid')
        mock_muranoclient.environments.get.assert_called_once_with(
            mock.sentinel.environment_id)
        mock_log.info.assert_has_calls([
            mock.call("Can not find environment_id sentinel.environment_id"
                      ", will create a new one."),
            mock.call("Cloud Foundry foo_space_guid remapped to "
                      "sentinel.alt_environment_id")
        ])

    @mock.patch.object(api, 'uuid', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    def test_provision_with_dict_parameters(self, mock_get_muranoclient,
                                            mock_db_cf, mock_uuid):
        test_body = {
            'space_guid': 'foo_space_guid',
            'organization_guid': 'foo_organization_guid',
            'plan_id': 'foo_plan_id',
            'service_id': 'foo_service_id',
            'parameters': {
                'foo': {
                    '?': {
                        'bar': 'baz'
                    }
                }
            }
        }
        test_headers = {
            'X-Auth-Token': mock.sentinel.token
        }
        mock_request = mock.Mock(body=json.dumps(test_body),
                                 headers=test_headers)
        mock_package = mock_get_muranoclient.return_value.packages.get.\
            return_value
        mock_service = mock.MagicMock()
        self.controller._make_service = mock.Mock(return_value=mock_service)
        mock_uuid.uuid4.return_value.hex = mock.sentinel.uuid

        resp = self.controller.provision(mock_request, None, None)

        self.assertEqual(202, resp.status_code)
        self.assertEqual({}, resp.json_body)
        self.controller._make_service.assert_called_once_with(
            'foo_space_guid', mock_package, 'foo_plan_id')
        mock_service.update.assert_called_once_with(
            {'foo': {'?': {'bar': 'baz', 'id': mock.sentinel.uuid}}})

    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_deprovision_with_missing_service(self, mock_db_cf):
        mock_db_cf.get_service_for_instance.return_value = None
        self.assertEqual({}, self.controller.deprovision(None, None))
        mock_db_cf.get_service_for_instance.assert_called_once_with(None)

    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_bind_with_missing_service(self, mock_db_cf):
        mock_db_cf.get_service_for_instance.return_value = None
        self.assertEqual({}, self.controller.bind(None, None, None, None))
        mock_db_cf.get_service_for_instance.assert_called_once_with(None)

    @mock.patch.object(api, 'LOG', autospec=True)
    @mock.patch.object(api.Controller, '_get_service', autospec=True)
    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_bind_except_key_error(self, mock_db_cf, mock_get_muranoclient,
                                   mock_get_service, mock_log):
        mock_db_service = mock.Mock(
            service_id=mock.sentinel.service_id,
            environment_id=mock.sentinel.environment_id)
        test_service = {}
        test_request = mock.Mock(
            headers={'X-Auth-Token': mock.sentinel.auth_token})

        mock_db_cf.get_service_for_instance.return_value = mock_db_service
        mock_get_service.return_value = test_service

        m_cli = mock_get_muranoclient.return_value
        m_env = m_cli.environments.get.return_value

        resp = self.controller.bind(test_request, None, None, None)

        self.assertEqual(500, resp.status_code)
        m_cli.environments.get.assert_called_once_with(
            mock.sentinel.environment_id, mock.ANY)
        mock_get_service.assert_called_once_with(self.controller, m_env,
                                                 mock.sentinel.service_id)
        mock_log.warning.assert_called_once_with(
            "This application doesn't have actions at all")

    @mock.patch.object(api, 'LOG', autospec=True)
    @mock.patch.object(api.Controller, '_get_service', autospec=True)
    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_bind_without_get_credentials(self, mock_db_cf,
                                          mock_get_muranoclient,
                                          mock_get_service, mock_log):
        mock_db_service = mock.Mock(
            service_id=mock.sentinel.service_id,
            environment_id=mock.sentinel.environment_id)
        test_service = {'?': {'_actions': []}}
        test_request = mock.Mock(
            headers={'X-Auth-Token': mock.sentinel.auth_token})

        mock_db_cf.get_service_for_instance.return_value = mock_db_service
        mock_get_service.return_value = test_service

        m_cli = mock_get_muranoclient.return_value
        m_env = m_cli.environments.get.return_value

        resp = self.controller.bind(test_request, None, None, None)

        self.assertEqual(500, resp.status_code)
        m_cli.environments.get.assert_called_once_with(
            mock.sentinel.environment_id, mock.ANY)
        mock_get_service.assert_called_once_with(self.controller, m_env,
                                                 mock.sentinel.service_id)
        mock_log.warning.assert_called_once_with(
            "This application doesn't have action getCredentials")

    def test_unbind(self):
        self.assertEqual({}, self.controller.unbind(None, None, None))

    @mock.patch.object(api, 'LOG', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_get_last_operation_without_service(self, mock_db_cf, mock_log):
        mock_db_cf.get_service_for_instance.return_value = None

        resp = self.controller.get_last_operation(
            None, mock.sentinel.instance_id)

        self.assertEqual(410, resp.status_code)
        self.assertEqual({}, resp.json_body)
        mock_log.warning.assert_called_once_with(
            'Requested service for instance sentinel.instance_id is not '
            'found')

    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_get_last_operation_succeeded(self, mock_db_cf,
                                          mock_get_muranoclient):
        mock_service = mock.Mock(
            environment_id=mock.sentinel.environment_id)
        mock_request = mock.Mock(
            headers={'X-Auth-Token': mock.sentinel.auth_token})
        mock_db_cf.get_service_for_instance.return_value = mock_service

        m_cli = mock_get_muranoclient.return_value
        m_env = m_cli.environments.get.return_value
        m_env.status = 'ready'

        resp = self.controller.get_last_operation(
            mock_request, mock.sentinel.instance_id)

        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            {'state': 'succeeded', 'description': 'operation succeed'},
            resp.json_body)
        mock_get_muranoclient.assert_called_once_with(mock.sentinel.auth_token,
                                                      mock_request)
        m_cli.environments.get.assert_called_once_with(
            mock.sentinel.environment_id)

    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_get_last_operation_in_progress(self, mock_db_cf,
                                            mock_get_muranoclient):
        mock_service = mock.Mock(
            environment_id=mock.sentinel.environment_id)
        mock_request = mock.Mock(
            headers={'X-Auth-Token': mock.sentinel.auth_token})
        mock_db_cf.get_service_for_instance.return_value = mock_service

        m_cli = mock_get_muranoclient.return_value
        m_env = m_cli.environments.get.return_value

        progress_statuses = ['pending', 'deleting', 'deploying']
        for status in progress_statuses:
            m_env.status = status

            resp = self.controller.get_last_operation(
                mock_request, mock.sentinel.instance_id)

            self.assertEqual(202, resp.status_code)
            self.assertEqual(
                {'state': 'in progress',
                 'description': 'operation in progress'},
                resp.json_body)
            mock_get_muranoclient.assert_called_once_with(
                mock.sentinel.auth_token, mock_request)
            m_cli.environments.get.assert_called_once_with(
                mock.sentinel.environment_id)
            mock_get_muranoclient.reset_mock()
            m_cli.environments.get.reset_mock()

    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_get_last_operation_failed(self, mock_db_cf,
                                       mock_get_muranoclient):
        mock_service = mock.Mock(
            environment_id=mock.sentinel.environment_id)
        mock_request = mock.Mock(
            headers={'X-Auth-Token': mock.sentinel.auth_token})
        mock_db_cf.get_service_for_instance.return_value = mock_service

        m_cli = mock_get_muranoclient.return_value
        m_env = m_cli.environments.get.return_value

        failed_statuses = ['deploy failure', 'delete failure']
        for status in failed_statuses:
            m_env.status = status

            resp = self.controller.get_last_operation(
                mock_request, mock.sentinel.instance_id)

            self.assertEqual(200, resp.status_code)
            self.assertEqual(
                {'state': 'failed',
                 'description': '{0}. Please correct it manually'
                 .format(status)},
                resp.json_body)
            mock_get_muranoclient.assert_called_once_with(
                mock.sentinel.auth_token, mock_request)
            m_cli.environments.get.assert_called_once_with(
                mock.sentinel.environment_id)
            mock_get_muranoclient.reset_mock()
            m_cli.environments.get.reset_mock()

    @mock.patch.object(api, '_get_muranoclient', autospec=True)
    @mock.patch.object(api, 'db_cf', autospec=True)
    def test_get_last_operation_unknown_status(self, mock_db_cf,
                                               mock_get_muranoclient):
        mock_service = mock.Mock(
            environment_id=mock.sentinel.environment_id)
        mock_request = mock.Mock(
            headers={'X-Auth-Token': mock.sentinel.auth_token})
        mock_db_cf.get_service_for_instance.return_value = mock_service

        m_cli = mock_get_muranoclient.return_value
        m_env = m_cli.environments.get.return_value

        m_env.status = 'unknown'

        resp = self.controller.get_last_operation(
            mock_request, mock.sentinel.instance_id)

        self.assertEqual(500, resp.status_code)
        self.assertEqual(
            {'state': 'unknown', 'description': 'operation unknown'},
            resp.json_body)
        mock_get_muranoclient.assert_called_once_with(
            mock.sentinel.auth_token, mock_request)
        m_cli.environments.get.assert_called_once_with(
            mock.sentinel.environment_id)

    @mock.patch.object(api, 'muranoclient', autospec=True)
    @mock.patch.object(api, 'glare_client', autospec=True)
    def test_get_muranoclient(self, mock_glare_client, mock_muranoclient):
        self._override_conf()

        m_artifacts_client = mock.Mock()
        m_muranoclient = mock.Mock()
        mock_glare_client.Client.return_value = m_artifacts_client
        mock_muranoclient.Client.return_value = m_muranoclient

        client = api._get_muranoclient(mock.sentinel.token_id, None)

        self.assertEqual(m_muranoclient, client)
        mock_glare_client.Client.assert_called_once_with(
            endpoint='foo_glare_url', token=mock.sentinel.token_id,
            insecure=True, key_file='foo_key_file', ca_file='foo_ca_file',
            cert_file='foo_cert_file', type_name='murano', type_version=1)
        mock_muranoclient.Client.assert_called_once_with(
            1, 'foo_murano_url', token=mock.sentinel.token_id,
            artifacts_client=m_artifacts_client)

    @mock.patch.object(api, 'LOG', autospec=True)
    @mock.patch.object(api, 'muranoclient', autospec=True)
    @mock.patch.object(api, 'glare_client', autospec=True)
    def test_get_muranoclient_without_urls(self, mock_glare_client,
                                           mock_muranoclient, mock_log):
        self._override_conf(without_urls=True)

        m_artifacts_client = mock.Mock()
        m_muranoclient = mock.Mock()
        mock_glare_client.Client.return_value = m_artifacts_client
        mock_muranoclient.Client.return_value = m_muranoclient
        mock_request = mock.Mock(endpoints={'murano': None})

        client = api._get_muranoclient(mock.sentinel.token_id, mock_request)

        self.assertEqual(m_muranoclient, client)
        mock_glare_client.Client.assert_called_once_with(
            endpoint=None, token=mock.sentinel.token_id,
            insecure=True, key_file='foo_key_file', ca_file='foo_ca_file',
            cert_file='foo_cert_file', type_name='murano', type_version=1)
        mock_muranoclient.Client.assert_called_once_with(
            1, None, token=mock.sentinel.token_id,
            artifacts_client=m_artifacts_client)
        mock_log.error.assert_has_calls([
            mock.call('No glare url is specified and no "artifact" '
                      'service is registered in keystone.'),
            mock.call('No murano url is specified and no '
                      '"application-catalog" service is registered in '
                      'keystone.')
        ])

    def _override_conf(self, without_urls=False):
        if without_urls:
            self.override_config('url', None, group='glare')
            self.override_config('url', None, group='murano')
        else:
            self.override_config('url', 'foo_glare_url', group='glare')
            self.override_config('url', 'foo_murano_url', group='murano')
        for arg, group, override_val in (
                ('packages_service', 'engine', 'glare'),
                ('insecure', 'glare', True),
                ('key_file', 'glare', 'foo_key_file'),
                ('ca_file', 'glare', 'foo_ca_file'),
                ('cert_file', 'glare', 'foo_cert_file')):
            self.override_config(arg, override_val, group=group)

    def test_resource(self):
        self.assertIsInstance(api.create_resource(), wsgi.Resource)
