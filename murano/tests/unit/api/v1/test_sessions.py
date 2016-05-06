# Copyright (c) 2015 Mirantis Inc.
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

import json

from oslo_config import fixture as config_fixture

from murano.api.v1 import environments
from murano.api.v1 import sessions
import murano.tests.unit.api.base as tb


class TestSessionsApi(tb.ControllerTest, tb.MuranoApiTestCase):
    def setUp(self):
        super(TestSessionsApi, self).setUp()
        self.environments_controller = environments.Controller()
        self.sessions_controller = sessions.Controller()
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])

    def test_cant_deploy_from_another_tenant(self):
        """Test to prevent deployment under another tenant user's creds

        If user from one tenant uses session id and environment id
        of user from another tenant - he is not able to deploy
        the environment.

        Bug: #1382026
        """
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        CREDENTIALS_2 = {'tenant': 'test_tenant_2', 'user': 'test_user_2'}

        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment for user #1
        request = self._post(
            '/environments', json.dumps({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = json.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])

        ENVIRONMENT_ID = response_body['id']

        # Create session of user #1
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            '',
            **CREDENTIALS_1
        )
        response_body = json.loads(request.get_response(self.api).body)

        SESSION_ID = response_body['id']

        # Deploy the environment using environment id and session id of user #1
        # by user #2
        request = self._post(
            '/environments/{environment_id}/sessions/'
            '{session_id}/deploy'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            '',
            **CREDENTIALS_2
        )
        response = request.get_response(self.api)

        # Should be forbidden!
        self.assertEqual(403, response.status_code)
