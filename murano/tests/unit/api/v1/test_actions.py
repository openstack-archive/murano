# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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
from oslo_utils import timeutils
from webob import exc

from murano.api.v1 import actions
from murano.common import policy
from murano.db import models
from murano.db import session as db_session
from murano.services import states
import murano.tests.unit.api.base as tb
import murano.tests.unit.utils as test_utils


@mock.patch.object(policy, 'check')
class TestActionsApi(tb.ControllerTest, tb.MuranoApiTestCase):

    def setUp(self):
        super(TestActionsApi, self).setUp()
        self.controller = actions.Controller()

    def test_execute_action(self, mock_policy_check):
        """Test that action execution results in the correct rpc call."""
        self._set_policy_rules(
            {'execute_action': '@'}
        )

        fake_now = timeutils.utcnow()
        expected = dict(
            id='12345',
            name='my-env',
            version=0,
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'Objects': {
                    '?': {'id': '12345',
                          '_actions': {
                              'actionsID_action': {
                                  'enabled': True,
                                  'name': 'Testaction'
                              }
                          }}
                },
                'Attributes': {}
            }
        )
        e = models.Environment(**expected)
        test_utils.save_models(e)

        rpc_task = {
            'action': {
                'args': '{}',
                'method': 'Testaction',
                'object_id': '12345'
            },
            'project_id': self.tenant,
            'user_id': self.user,
            'model': {
                'Attributes': {},
                'Objects': {
                    'applications': [],
                    '?': {
                        '_actions': {
                            'actionsID_action': {
                                'enabled': True,
                                'name': 'Testaction'
                            }
                        },
                        'id': '12345'
                    }
                }
            },
            'token': None,
            'id': '12345'
        }

        req = self._post('/environments/12345/actions/actionID_action', b'{}')
        result = self.controller.execute(req, '12345', 'actionsID_action',
                                         '{}')

        self.mock_engine_rpc.handle_task.assert_called_once_with(rpc_task)

        self.assertIn('task_id', result)

    def _create_session_with_state(self, environment, user_id, state):
        unit = db_session.get_session()
        session = models.Session()
        session.environment_id = environment.id
        session.user_id = user_id
        session.state = state
        session.version = environment.version
        with unit.begin():
            unit.add(session)

    def test_execute_action_with_session_in_deploying_state(self, _):
        """Test whether session in the deploying state throws error."""
        self._set_policy_rules(
            {'execute_action': '@'}
        )

        fake_now = timeutils.utcnow()
        expected = dict(
            id='12345',
            name='my-env',
            version=0,
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'Objects': {
                    '?': {'id': '12345',
                          '_actions': {
                              'actionsID_action': {
                                  'enabled': True,
                                  'name': 'Testaction'
                              }
                          }}
                },
                'Attributes': {}
            }
        )
        environment = models.Environment(**expected)
        test_utils.save_models(environment)
        req = self._post('/environments/12345/actions/actionID_action', b'{}')
        user_id = req.context.user

        self._create_session_with_state(environment, user_id,
                                        states.SessionState.DEPLOYING)
        self.assertRaises(exc.HTTPForbidden, self.controller.execute,
                          req, '12345', 'actionsID_action', {})

    def test_execute_action_with_session_in_deleting_state(self, _):
        """Test whether session in deleting state throws error."""
        self._set_policy_rules(
            {'execute_action': '@'}
        )

        fake_now = timeutils.utcnow()
        expected = dict(
            id='12345',
            name='my-env',
            version=0,
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'Objects': {
                    '?': {'id': '12345',
                          '_actions': {
                              'actionsID_action': {
                                  'enabled': True,
                                  'name': 'Testaction'
                              }
                          }}
                },
                'Attributes': {}
            }
        )
        environment = models.Environment(**expected)
        test_utils.save_models(environment)
        req = self._post('/environments/12345/actions/actionID_action', b'{}')
        user_id = req.context.user

        self._create_session_with_state(environment, user_id,
                                        states.SessionState.DELETING)
        self.assertRaises(exc.HTTPForbidden, self.controller.execute,
                          req, '12345', 'actionsID_action', {})

    @mock.patch('murano.db.services.sessions.SessionServices.validate')
    def test_execute_action_with_invalid_session_version(self, mocked_function,
                                                         _):
        """Test whether validate session function throws error."""
        self._set_policy_rules(
            {'execute_action': '@'}
        )

        fake_now = timeutils.utcnow()
        expected = dict(
            id='12345',
            name='my-env',
            version=0,
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'Objects': {
                    '?': {'id': '12345',
                          '_actions': {
                              'actionsID_action': {
                                  'enabled': True,
                                  'name': 'Testaction'
                              }
                          }}
                },
                'Attributes': {}
            }
        )
        environment = models.Environment(**expected)
        test_utils.save_models(environment)
        req = self._post('/environments/12345/actions/actionID_action', b'{}')

        mocked_function.return_value = False
        self.assertRaises(exc.HTTPForbidden, self.controller.execute,
                          req, '12345', 'actionsID_action', {})

    def test_get_result(self, _):
        """Result of task with given id and environment id is returned."""
        now = timeutils.utcnow()
        expected_environment_id = 'test_environment'
        expected_task_id = 'test_task'
        expected_result = {'test_result': 'test_result'}

        environment = models.Environment(
            id=expected_environment_id,
            name='test_environment', created=now, updated=now,
            tenant_id=self.tenant
        )

        task = models.Task(
            id=expected_task_id,
            started=now,
            finished=now,
            result=expected_result,
            environment_id=expected_environment_id
        )

        test_utils.save_models(environment, task)

        request = self._get(
            '/environments/{environment_id}/actions/{task_id}'
            .format(environment_id=expected_environment_id,
                    task_id=expected_task_id),
        )

        response = request.get_response(self.api)

        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_result, response.json)

    def test_get_result_not_found(self, _):
        """Return 404 on null task

        If task does not exist, it should be handled correctly
        and API should return 404.
        """
        expected_environment_id = 'test_environment'

        environment = models.Environment(
            id=expected_environment_id,
            name='test_environment',
            tenant_id=self.tenant
        )
        test_utils.save_models(environment)

        request = self._get(
            '/environments/{environment_id}/actions/{task_id}'
            .format(environment_id=expected_environment_id,
                    task_id='not_existent_task_id'),
        )

        response = request.get_response(self.api)

        self.assertEqual(404, response.status_code)
