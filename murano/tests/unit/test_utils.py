# Copyright (c) 2016 AT&T Corp
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
from webob import exc

from murano.services import states
import murano.tests.unit.base as test_base
from murano.tests.unit import utils as test_utils
from murano import utils


class TestUtils(test_base.MuranoTestCase):

    @mock.patch('murano.utils.db_session')
    def test_check_env(self, mock_db_session):
        """Test check env."""
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_env = mock.MagicMock(environment_id='test_env_id',
                                  tenant_id=mock_request.context.tenant)
        mock_db_session.get_session().query().get.return_value = mock_env

        env = utils.check_env(mock_request, mock_env.environment_id)
        self.assertEqual(mock_env, env)

    @mock.patch('murano.utils.db_session')
    def test_check_env_with_null_environment_id(self, mock_db_session):
        """Test check env with null environment id throws exception."""
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_db_session.get_session().query().get.return_value = None

        test_env_id = 'test_env_id'
        expected_error_message = 'Environment with id {env_id} not found'\
                                 .format(env_id=test_env_id)

        with self.assertRaisesRegex(exc.HTTPNotFound,
                                    expected_error_message):
            utils.check_env(mock_request, test_env_id)

    @mock.patch('murano.utils.db_session')
    def test_check_env_with_mismatching_tenant_id(self, mock_db_session):
        """Test check env without matching tenant ids throws exception."""
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_env = mock.MagicMock(environment_id='test_env_id',
                                  tenant_id='another_test_tenant_id')
        mock_db_session.get_session().query().get.return_value = mock_env

        expected_error_message = 'User is not authorized to access these '\
                                 'tenant resources'

        with self.assertRaisesRegex(exc.HTTPForbidden,
                                    expected_error_message):
            utils.check_env(mock_request, mock_env.environment_id)

    def test_check_session_with_null_session(self):
        """Test check session with null session throws exception."""
        expected_error_message = 'Session <SessionId {id}> is not found'\
                                 .format(id=None)
        with self.assertRaisesRegex(exc.HTTPNotFound,
                                    expected_error_message):
            utils.check_session(None, None, None, None)

    @mock.patch('murano.utils.check_env')
    def test_check_session_with_mismatching_environment_id(self, _):
        """Test check session without matching env ids throws exception."""
        mock_session = mock.MagicMock(session_id='session_id',
                                      environment_id='environment_id')
        environment_id = 'another_environment_id'
        expected_error_msg = 'Session <SessionId {session_id}> is not tied '\
                             'with Environment <EnvId {environment_id}>'\
                             .format(session_id=mock_session.session_id,
                                     environment_id=environment_id)
        with self.assertRaisesRegex(exc.HTTPBadRequest,
                                    expected_error_msg):
            utils.check_session(None, environment_id, mock_session,
                                mock_session.session_id)

    def test_verify_session_with_invalid_request_header(self):
        """Test session with invalid request header throws exception."""
        dummy_context = test_utils.dummy_context()
        if dummy_context.session:
            dummy_context.session = None
        mock_request = mock.MagicMock(context=dummy_context)
        expected_error_message = 'X-Configuration-Session header which '\
                                 'indicates to the session is missed'
        with self.assertRaisesRegex(exc.HTTPBadRequest,
                                    expected_error_message):
            self._test_verify_session(mock_request)

    @mock.patch('murano.utils.db_session')
    def test_verify_session_with_null_session(self, mock_db_session):
        """Test null session throws expected exception."""
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.session = mock.MagicMock(
            return_value='test_sess_id')
        mock_db_session.get_session().query().get.return_value = None
        expected_error_message = 'Session <SessionId {0}> is not found'\
                                 .format(mock_request.context.session)
        with self.assertRaisesRegex(exc.HTTPNotFound,
                                    expected_error_message):
            self._test_verify_session(mock_request)

    @mock.patch('murano.utils.db_session')
    def test_verify_env_template_with_invalid_tenant(self, mock_db_session):
        """Test session validation failure throws expected exception."""
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.tenant = mock.MagicMock(
            return_value='test_tenant_id')
        mock_env_template = mock.MagicMock(tenant_id='another_test_tenant_id')
        mock_db_session.get_session().query().get.return_value =\
            mock_env_template
        expected_error_message = 'User is not authorized to access this'\
                                 ' tenant resources'
        with self.assertRaisesRegex(exc.HTTPForbidden,
                                    expected_error_message):
            self._test_verify_env_template(mock_request, None)

    @mock.patch('murano.utils.db_session')
    def test_verify_env_template_with_null_template(self, mock_db_session):
        """Test null env template throws expected exception."""
        mock_db_session.get_session().query().get.return_value = None
        expected_error_message = 'Environment Template with id {id} not found'\
                                 .format(id='test_env_template_id')
        with self.assertRaisesRegex(exc.HTTPNotFound,
                                    expected_error_message):
            self._test_verify_env_template(None, 'test_env_template_id')

    @utils.verify_env_template
    def _test_verify_env_template(self, request, env_template_id):
        """Helper function for testing above decorator."""
        pass

    @mock.patch('murano.utils.sessions.SessionServices.validate')
    @mock.patch('murano.utils.db_session')
    def test_verify_session_with_invalid_session(self, mock_db_session,
                                                 mock_validate):
        """Test session validation failure throws expected exception."""
        mock_validate.return_value = False
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.session = mock.MagicMock(
            return_value='test_sess_id')
        mock_db_session.get_session().query().get.return_value =\
            mock.MagicMock()
        expected_error_message = 'Session <SessionId {0}> is invalid: '\
                                 'environment has been updated or '\
                                 'updating right now with other session'\
                                 .format(mock_request.context.session)
        with self.assertRaisesRegex(exc.HTTPForbidden,
                                    expected_error_message):
            self._test_verify_session(mock_request)

    @mock.patch('murano.utils.sessions.SessionServices.validate')
    @mock.patch('murano.utils.db_session')
    def test_verify_session_in_deploying_state(self,
                                               mock_db_session,
                                               mock_validate):
        """Test deploying session throws expected exception."""
        mock_validate.return_value = True
        mock_request = mock.MagicMock(context=test_utils.dummy_context())
        mock_request.context.session = mock.MagicMock(
            return_value='test_sess_id')
        mock_db_session.get_session().query().get.return_value =\
            mock.MagicMock(state=states.SessionState.DEPLOYING)
        expected_error_message = 'Session <SessionId {0}> is already in '\
                                 'deployment state'\
                                 .format(mock_request.context.session)
        with self.assertRaisesRegex(exc.HTTPForbidden,
                                    expected_error_message):
            self._test_verify_session(mock_request)

    @utils.verify_session
    def _test_verify_session(self, request):
        """Helper function for testing above decorator."""
        pass
