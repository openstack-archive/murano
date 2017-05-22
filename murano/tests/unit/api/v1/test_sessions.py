# Copyright (c) 2015 Mirantis Inc.
# Copyright (c) 2016 AT&T Corp
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
from oslo_config import fixture as config_fixture
from oslo_serialization import jsonutils
from webob import exc

from murano.api.v1 import environments
from murano.api.v1 import sessions
from murano.services import states
import murano.tests.unit.api.base as tb
from murano.tests.unit import utils as test_utils


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
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])

        ENVIRONMENT_ID = response_body['id']

        # Create session of user #1
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)

        SESSION_ID = response_body['id']

        # Deploy the environment using environment id and session id of user #1
        # by user #2
        request = self._post(
            '/environments/{environment_id}/sessions/'
            '{session_id}/deploy'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS_2
        )
        response = request.get_response(self.api)

        # Should be forbidden!
        self.assertEqual(403, response.status_code)

    def test_session_show(self):
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        CREDENTIALS_2 = {'tenant': 'test_tenant_2', 'user': 'test_user_2'}

        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment for user #1
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])
        ENVIRONMENT_ID = response_body['id']

        # Create session of user #1
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']

        # Show environment with correct credentials
        request = self._get(
            '/environments/{environment_id}/sessions/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(SESSION_ID, response_body['id'])

        # Show environment with incorrect credentials
        request = self._get(
            '/environments/{environment_id}/sessions/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS_2
        )
        response = request.get_response(self.api)
        self.assertEqual(403, response.status_code)

    def test_session_delete(self):
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}

        self._set_policy_rules(
            {'create_environment': '@'}
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

        # Create session
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']

        # Delete session
        request = self._delete(
            '/environments/{environment_id}/delete/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS
        )
        response = self.sessions_controller.delete(
            request, ENVIRONMENT_ID, SESSION_ID)

        # Make sure the session was deleted
        request = self._get(
            '/environments/{environment_id}/sessions/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS
        )
        response = request.get_response(self.api)
        self.assertEqual(404, response.status_code)

    @mock.patch('murano.api.v1.sessions.sessions.SessionServices')
    @mock.patch('murano.api.v1.sessions.envs')
    @mock.patch('murano.api.v1.sessions.check_env')
    def test_configure(self, _, mock_envs, mock_session_services):
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_session = mock.MagicMock(to_dict=mock.MagicMock(
            return_value={'test_env_id', 'test_user_id'}))
        mock_session_services.create.return_value = mock_session

        result = self.sessions_controller.configure(
            mock_request, 'test_env_id')
        self.assertEqual({'test_env_id', 'test_user_id'}, result)

    @mock.patch('murano.api.v1.sessions.envs')
    @mock.patch('murano.api.v1.sessions.check_env')
    def test_configure_with_env_in_illegal_state(self, _, mock_envs):
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        illegal_states = [states.EnvironmentStatus.DEPLOYING,
                          states.EnvironmentStatus.DELETING]
        expected_error_msg = 'Could not open session for environment '\
                             '<EnvId: {env_id}>, environment has '\
                             'deploying or deleting status.'\
                             .format(env_id='test_env_id')

        for state in illegal_states:
            mock_envs.EnvironmentServices.get_status.return_value = state

            with self.assertRaisesRegex(exc.HTTPForbidden,
                                        expected_error_msg):
                self.sessions_controller.configure(mock_request, 'test_env_id')

    @mock.patch('murano.api.v1.sessions.check_session')
    @mock.patch('murano.api.v1.sessions.db_session')
    def test_show_with_invalid_user(self, mock_db_session, _):
        mock_session = mock.MagicMock(user_id='test_user_id')
        mock_db_session.get_session().query().get.return_value = mock_session
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.user = 'another_test_user_id'
        expected_error_msg = 'User <UserId {0}> is not authorized to '\
            'access session <SessionId {1}>.'\
            .format(mock_request.context.user, 'test_sess_id')

        with self.assertRaisesRegex(exc.HTTPUnauthorized,
                                    expected_error_msg):
            self.sessions_controller.show(mock_request, None, 'test_sess_id')

    @mock.patch('murano.api.v1.sessions.check_session')
    @mock.patch('murano.api.v1.sessions.sessions.SessionServices')
    @mock.patch('murano.api.v1.sessions.db_session')
    def test_show_with_invalid_session(self, mock_db_session,
                                       mock_session_services, _):
        mock_session = mock.MagicMock(user_id='test_user_id')
        mock_db_session.get_session().query().get.return_value = mock_session
        mock_session_services.validate.return_value = False
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.user = 'test_user_id'
        expected_error_msg = 'Session <SessionId {0}> is invalid: environment'\
                             ' has been updated or updating right now with'\
                             ' other session'.format('test_sess_id')

        with self.assertRaisesRegex(exc.HTTPForbidden,
                                    expected_error_msg):
            self.sessions_controller.show(mock_request, None, 'test_sess_id')

    @mock.patch('murano.api.v1.sessions.check_session')
    @mock.patch('murano.api.v1.sessions.db_session')
    def test_delete_with_invalid_user(self, mock_db_session, _):
        mock_session = mock.MagicMock(user_id='test_user_id')
        mock_db_session.get_session().query().get.return_value = mock_session
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.user = 'another_test_user_id'
        expected_error_msg = 'User <UserId {0}> is not authorized to '\
            'access session <SessionId {1}>.'\
            .format(mock_request.context.user, 'test_sess_id')

        with self.assertRaisesRegex(exc.HTTPUnauthorized,
                                    expected_error_msg):
            self.sessions_controller.delete(mock_request, None, 'test_sess_id')

    @mock.patch('murano.api.v1.sessions.check_session')
    @mock.patch('murano.api.v1.sessions.sessions.SessionServices')
    @mock.patch('murano.api.v1.sessions.db_session')
    def test_delete_with_deploying_session(self, mock_db_session,
                                           mock_session_services, _):
        mock_session = mock.MagicMock(user_id='test_user_id',
                                      state=states.SessionState.DEPLOYING)
        mock_db_session.get_session().query().get.return_value = mock_session
        mock_session_services.validate.return_value = False
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.user = 'test_user_id'
        expected_error_msg = 'Session <SessionId: {0}> is in deploying '\
                             'state and could not be deleted'\
                             .format('test_sess_id')

        with self.assertRaisesRegex(exc.HTTPForbidden,
                                    expected_error_msg):
            self.sessions_controller.delete(mock_request, None, 'test_sess_id')

    @mock.patch('murano.api.v1.sessions.check_session')
    @mock.patch('murano.api.v1.sessions.sessions.SessionServices')
    @mock.patch('murano.api.v1.sessions.db_session')
    def test_deploy_with_invalid_session(self, mock_db_session,
                                         mock_session_services, _):
        mock_db_session.get_session().query().get.return_value = None
        mock_session_services.validate.return_value = False
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        expected_error_msg = 'Session <SessionId {0}> is invalid: environment'\
                             ' has been updated or updating right now with'\
                             ' other session'.format('test_sess_id')

        with self.assertRaisesRegex(exc.HTTPForbidden,
                                    expected_error_msg):
            self.sessions_controller.deploy(mock_request, None, 'test_sess_id')

    @mock.patch('murano.api.v1.sessions.check_session')
    @mock.patch('murano.api.v1.sessions.sessions.SessionServices')
    @mock.patch('murano.api.v1.sessions.db_session')
    def test_deploy_with_session_in_invalid_state(self, mock_db_session,
                                                  mock_session_services, _):
        mock_session_services.validate.return_value = True
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        expected_error_msg = 'Session <SessionId {0}> is already deployed or '\
                             'deployment is in progress'.format('test_sess_id')

        invalid_states = [states.SessionState.DEPLOYING,
                          states.SessionState.DEPLOYED,
                          states.SessionState.DEPLOY_FAILURE,
                          states.SessionState.DELETING,
                          states.SessionState.DELETE_FAILURE]

        for state in invalid_states:
            mock_session = mock.MagicMock(state=state)
            mock_db_session.get_session().query().get.return_value =\
                mock_session
            with self.assertRaisesRegex(exc.HTTPForbidden,
                                        expected_error_msg):
                self.sessions_controller.deploy(
                    mock_request, None, 'test_sess_id')
