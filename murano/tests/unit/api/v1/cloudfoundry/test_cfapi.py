#    Copyright (c) 2015 Mirantis, Inc.
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
from murano.tests.unit import base


class TestController(base.MuranoTestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.controller = api.Controller()

        self.request = mock.MagicMock()
        auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        self.request.headers = {'Authorization': auth,
                                'X-Auth-Token': 'foo-bar',
                                'X-Project-Id': 'bar-baz'}

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
    @mock.patch('murano.db.catalog.api.package_get')
    @mock.patch('murano.cfapi.cfapi._get_muranoclient')
    @mock.patch('murano.db.services.cf_connections.set_instance_for_service')
    @mock.patch('murano.db.services.cf_connections.set_environment_for_space')
    @mock.patch('murano.db.services.cf_connections.set_tenant_for_org')
    @mock.patch('murano.db.services.cf_connections.get_environment_for_space')
    @mock.patch('murano.db.services.cf_connections.get_tenant_for_org')
    def test_provision_existent(self, mock_get_tenant,
                                mock_get_environment, mock_set_tenant,
                                mock_set_environment, mock_is, mock_client,
                                mock_package, mock_policy):

        body = {"space_guid": "s1-p1",
                "organization_guid": "o1-r1",
                "plan_id": "p1-l1",
                "service_id": "s1-e1",
                "parameters": {'some_parameter': 'value',
                               '?': {}}}
        self.request.body = json.dumps(body)

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
