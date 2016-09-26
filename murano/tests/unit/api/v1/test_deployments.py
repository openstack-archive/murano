# Copyright (c) 2016 AT&T Inc.
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

import mock
import murano.tests.unit.api.base as tb

from oslo_config import fixture as config_fixture
from oslo_serialization import jsonutils

from murano.api.v1 import deployments
from murano.api.v1 import environments

from webob import exc


class TestDeploymentsApi(tb.ControllerTest, tb.MuranoApiTestCase):
    def setUp(self):
        super(TestDeploymentsApi, self).setUp()
        self.environments_controller = environments.Controller()
        self.deployments_controller = deployments.Controller()
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])

    def test_deployments_index(self):
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@',
             'list_deployments': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS['tenant'],
                         response_body['tenant_id'])

        ENVIRONMENT_ID = response_body['id']

        self.expect_policy_check('list_deployments',
                                 {'environment_id': ENVIRONMENT_ID})
        result = self.deployments_controller.index(request, ENVIRONMENT_ID)
        self.assertEqual([], result['deployments'])

    def test_deployments_not_found_statuses(self):
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@',
             'statuses_deployments': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post('/environments', jsonutils.
                             dump_as_bytes({'name': 'test_environment_1'}),
                             **CREDENTIALS)
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS['tenant'],
                         response_body['tenant_id'])

        ENVIRONMENT_ID = response_body['id']
        deploy_id = '1'
        self.expect_policy_check('statuses_deployments',
                                 {'deployment_id': deploy_id,
                                  'environment_id': ENVIRONMENT_ID})
        self.assertRaises(exc.HTTPNotFound,
                          self.deployments_controller.statuses, request,
                          ENVIRONMENT_ID, deploy_id)

    def test_deployments_status(self):
        CREDENTIALS = {'tenant': 'test_tenant', 'user': 'test_user'}
        self._set_policy_rules(
            {'create_environment': '@',
             'statuses_deployments': '@',
             'list_deployments': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS['tenant'],
                         response_body['tenant_id'])

        ENVIRONMENT_ID = response_body['id']

        # Create session
        request = self._post('/environments/{environment_id}/configure'
                             .format(environment_id=ENVIRONMENT_ID),
                             b'', **CREDENTIALS)
        response_body = jsonutils.loads(request.get_response(self.api).body)

        SESSION_ID = response_body['id']

        request = self._post('/environments/{environment_id}/sessions/'
                             '{session_id}/deploy'
                             .format(environment_id=ENVIRONMENT_ID,
                                     session_id=SESSION_ID),
                             b'', **CREDENTIALS)
        request.get_response(self.api)

        self.expect_policy_check('list_deployments',
                                 {'environment_id': ENVIRONMENT_ID})
        result = self.deployments_controller.index(request, ENVIRONMENT_ID)
        deploy_id = result['deployments'][0]['id']

        self.expect_policy_check('statuses_deployments',
                                 {'deployment_id': deploy_id,
                                  'environment_id': ENVIRONMENT_ID})
        result = self.deployments_controller.statuses(request, ENVIRONMENT_ID,
                                                      deploy_id)
        self.assertNotEqual(result['reports'], [])

        request.GET['service_id'] = "12"
        self.expect_policy_check('statuses_deployments',
                                 {'deployment_id': deploy_id,
                                  'environment_id': ENVIRONMENT_ID})
        result = self.deployments_controller.statuses(request, ENVIRONMENT_ID,
                                                      deploy_id)
        self.assertEqual(result['reports'], [])

        self.expect_policy_check('statuses_deployments',
                                 {'deployment_id': deploy_id,
                                  'environment_id': '12'})
        self.assertRaises(exc.HTTPBadRequest,
                          self.deployments_controller.statuses, request,
                          "12", deploy_id)

    def test_set_dep_state(self):
        deployment = mock.Mock()
        deployment.id = "1"
        deployment.description = {'applications': []}
        unit = mock.Mock()
        query_result = mock.Mock()
        filter_by_result = mock.Mock()
        filter_by_result.count.return_value = 0
        query_result.filter_by.return_value = filter_by_result
        unit.query.return_value = query_result

        result = deployments.set_dep_state(deployment, unit)
        self.assertEqual('success', result.state)

        deployment.description = None
        result = deployments.set_dep_state(deployment, unit)
        self.assertEqual('success', result.state)

        filter_by_result.count.return_value = 1
        query_result.filter_by.return_value = filter_by_result
        result = deployments.set_dep_state(deployment, unit)
        self.assertEqual('completed_w_errors', result.state)

        filter_by_result.count.return_value = 0
        query_result.filter_by.return_value = filter_by_result
        deployment.finished = False
        result = deployments.set_dep_state(deployment, unit)
        self.assertEqual('running', result.state)

        filter_by_result.count.return_value = 1
        query_result.filter_by.return_value = filter_by_result
        result = deployments.set_dep_state(deployment, unit)
        self.assertEqual('running_w_errors', result.state)
