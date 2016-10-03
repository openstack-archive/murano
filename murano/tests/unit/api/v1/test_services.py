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

from oslo_config import fixture as config_fixture
from oslo_serialization import jsonutils
from webob import exc

from murano.api.v1 import environments
from murano.api.v1 import services
from murano.api.v1 import sessions
import murano.tests.unit.api.base as tb


class TestServicesApi(tb.ControllerTest, tb.MuranoApiTestCase):

    def setUp(self):
        super(TestServicesApi, self).setUp()
        self.environments_controller = environments.Controller()
        self.sessions_controller = sessions.Controller()
        self.services_controller = services.Controller()
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])

    def test_can_post(self):
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])

        environment_id = response_body['id']

        # Create session
        request = self._post('/environments/{environment_id}/configure'
                             .format(environment_id=environment_id), b'',
                             **CREDENTIALS_1)
        response_body = jsonutils.loads(request.get_response(self.api).body)

        session_id = response_body['id']

        path = "/"

        request = self._post('/v1/environments/{0}/services'.
                             format(environment_id, session_id), b'',
                             **CREDENTIALS_1)
        request.headers['X-Configuration-Session'] = str(session_id)
        request.context.session = session_id

        self.assertRaises(exc.HTTPBadRequest, self.services_controller.post,
                          request, environment_id, path)

        response = self.services_controller.post(request, environment_id,
                                                 path, "test service")
        self.assertEqual("test service", response)

    def test_can_put(self):
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])

        environment_id = response_body['id']

        # Create session
        request = self._post('/environments/{environment_id}/configure'
                             .format(environment_id=environment_id), b'',
                             **CREDENTIALS_1)
        response_body = jsonutils.loads(request.get_response(self.api).body)

        session_id = response_body['id']

        path = "/"

        request = self._put('/v1/environments/{0}/services'.
                            format(environment_id, session_id), b'',
                            **CREDENTIALS_1)
        request.headers['X-Configuration-Session'] = str(session_id)
        request.context.session = session_id

        # Check that empty body can be put
        response = self.services_controller.put(request, environment_id,
                                                path, [])
        self.assertEqual([], response)

        response = self.services_controller.put(request, environment_id,
                                                path, "test service")
        self.assertEqual("test service", response)

    def test_can_get(self):
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])

        environment_id = response_body['id']

        # Create session
        request = self._post('/environments/{environment_id}/configure'
                             .format(environment_id=environment_id), b'',
                             **CREDENTIALS_1)
        response_body = jsonutils.loads(request.get_response(self.api).body)

        session_id = response_body['id']

        # Create service
        path = '/'
        request = self._post('/v1/environments/{0}/services'.
                             format(environment_id, session_id), b'',
                             **CREDENTIALS_1)
        request.headers['X-Configuration-Session'] = str(session_id)
        request.context.session = session_id

        response = self.services_controller.post(request, environment_id,
                                                 path, "test service")
        # Get service
        request = self._get('/v1/environments/{0}/services'.
                            format(environment_id), b'',
                            **CREDENTIALS_1)

        response = self.services_controller.get(request, environment_id, path)
        self.assertEqual([], response)

        request.headers['X-Configuration-Session'] = str(session_id)
        request.context.session = session_id

        response = self.services_controller.get(request, environment_id, path)
        self.assertNotEqual([], response)

    def test_can_delete(self):
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])

        environment_id = response_body['id']

        # Create session
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=environment_id),
            b'', **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)

        session_id = response_body['id']

        # Create service
        path = '/'
        request = self._post('/v1/environments/{0}/services'.
                             format(environment_id, session_id), b'',
                             **CREDENTIALS_1)
        request.headers['X-Configuration-Session'] = str(session_id)
        request.context.session = session_id

        self.services_controller.post(request, environment_id,
                                      path, "test service")

        # Delete service
        request = self._delete('/v1/environments/{0}/services'.
                               format(environment_id), b'',
                               **CREDENTIALS_1)

        self.assertRaises(exc.HTTPBadRequest, self.services_controller.delete,
                          request, environment_id, path)

        request.headers['X-Configuration-Session'] = str(session_id)
        request.context.session = session_id

        self.assertRaises(exc.HTTPNotFound, self.services_controller.delete,
                          request, environment_id, path)
