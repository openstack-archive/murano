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

from murano.services import actions
from murano.services import states
import murano.tests.unit.base as test_base


class TestActions(test_base.MuranoTestCase):

    def test_create_action_task(self):
        mock_action_name = 'test_action_name'
        mock_target_obj = '123'
        mock_args = {'param1': 'something', 'param2': 'something else'}
        mock_environment = mock.MagicMock(id='456', tenant_id='789')
        mock_description = {
            'Objects': {
                '?': {
                    'id': '456'
                },
                'applications': [],
                'services': ['service1', 'service2']
            },
            'project_id': 'XXX',
            'user_id': 'YYY'
        }
        mock_session = mock.MagicMock(description=mock_description)
        mock_context = mock.Mock(auth_token='test_token',
                                 tenant='test_tenant',
                                 user='test_user')
        expected_task = {
            'action': {
                'object_id': mock_target_obj,
                'method': mock_action_name,
                'args': mock_args
            },
            'model': {
                'Objects': {
                    '?': {
                        'id': mock_environment.id
                    },
                    'applications':
                        mock_session.description['Objects']['services']
                },
                'project_id': 'XXX',
                'user_id': 'YYY'
            },
            'token': 'test_token',
            'project_id': 'test_tenant',
            'user_id': 'test_user',
            'id': mock_environment.id
        }

        task = actions.ActionServices.create_action_task(mock_action_name,
                                                         mock_target_obj,
                                                         mock_args,
                                                         mock_environment,
                                                         mock_session,
                                                         mock_context)

        self.assertEqual(expected_task, task)

    @mock.patch('murano.services.actions.models')
    def test_update_task(self, mock_models):
        mock_models.Task = mock.MagicMock()
        mock_models.Status = mock.MagicMock()
        mock_action = [{}, {'name': 'test_action_name'}]
        mock_session = mock.MagicMock(environment_id='123',
                                      state=states.SessionState.OPENED,
                                      description={'Objects': ['o1', 'o2']})
        mock_task = {'action': 'test_action_name'}
        mock_unit = mock.MagicMock(__enter__=mock.MagicMock(),
                                   __exit__=mock.MagicMock())

        actions.ActionServices.update_task(mock_action, mock_session,
                                           mock_task, mock_unit)

        self.assertEqual(mock_session.environment_id,
                         mock_models.Task().environment_id)
        self.assertEqual(dict(mock_session.description['Objects']),
                         mock_models.Task().description)
        self.assertEqual(mock_task['action'],
                         mock_models.Task().action)
        self.assertIn(mock_action[1]['name'],
                      mock_models.Status().text)
        self.assertEqual('info', mock_models.Status().level)
        mock_models.Task().statuses.append.assert_called_once_with(
            mock_models.Status())
        self.assertEqual(2, mock_unit.add.call_count)
        expected_session = mock_session
        expected_session.state = states.SessionState.DEPLOYED
        mock_unit.add.assert_any_call(expected_session)
        mock_unit.add.assert_called_with(mock_models.Task())

    @mock.patch('murano.services.actions.rpc')
    @mock.patch('murano.services.actions.actions_db.update_task')
    @mock.patch('murano.services.actions.ActionServices.create_action_task')
    def test_submit_task(self, mock_create_action_task, mock_update_task,
                         mock_rpc):
        mock_task = mock.MagicMock()
        mock_create_action_task.return_value = mock_task
        mock_update_task.return_value = '123'
        mock_rpc.engine().handle_task = mock.MagicMock()

        test_action_name = 'test_action_name'
        test_target_obj = 'test_target_obj'
        test_args = 'test_args'
        test_environment = 'test_environment'
        test_session = 'test_session'
        context = mock.Mock()
        context.auth_token = 'test_token'
        context.tenant = 'test_tenant'
        context.user = 'test_user'
        test_unit = 'test_unit'

        task_id = actions.ActionServices.submit_task(test_action_name,
                                                     test_target_obj,
                                                     test_args,
                                                     test_environment,
                                                     test_session,
                                                     context,
                                                     test_unit)

        self.assertEqual('123', task_id)
        mock_create_action_task.assert_called_once_with(test_action_name,
                                                        test_target_obj,
                                                        test_args,
                                                        test_environment,
                                                        test_session,
                                                        context)
        mock_update_task.assert_called_once_with(test_action_name,
                                                 test_session, mock_task,
                                                 test_unit)
        mock_rpc.engine().handle_task.assert_called_once_with(mock_task)

    @mock.patch('murano.services.actions.actions_db.get_environment')
    @mock.patch('murano.services.actions.ActionServices.submit_task')
    def test_execute(self, mock_submit_task, mock_get_environment):
        mock_environment = mock.MagicMock()
        mock_task_id = 'test_task_id'
        mock_get_environment.return_value = mock_environment
        mock_submit_task.return_value = mock_task_id

        test_action_id = 'test_action_id'
        test_description = [{
            '?': {
                'id': 'test_obj_id',
                '_actions': {
                    test_action_id: {
                        'name': 'test_action_1',
                        'enabled': True
                    }
                }
            }
        }]
        test_session = mock.MagicMock(description=test_description)
        test_unit = 'test_unit'
        test_token = 'test_token'
        test_args = None
        expected_action_name = 'test_action_1'
        expected_target_obj = 'test_obj_id'

        task_id = actions.ActionServices.execute(test_action_id, test_session,
                                                 test_unit, test_token,
                                                 test_args)

        self.assertEqual(mock_task_id, task_id)
        mock_submit_task.assert_called_once_with(expected_action_name,
                                                 expected_target_obj,
                                                 {}, mock_environment,
                                                 test_session, test_token,
                                                 test_unit)

    @mock.patch('murano.services.actions.actions_db.get_environment')
    def test_execute_with_invalid_action_id(self, mock_get_environment):
        test_action_id = 'test_action_id'
        test_session = mock.MagicMock(description=[])

        with self.assertRaisesRegex(LookupError, 'Action is not found'):
            actions.ActionServices.execute(test_action_id, test_session,
                                           None, None, None)

    @mock.patch('murano.services.actions.actions_db.get_environment')
    def test_execute_with_disabled_action(self, mock_get_environment):
        test_action_id = 'test_action_id'
        test_description = [{
            '?': {
                'id': 'test_obj_id',
                '_actions': {
                    test_action_id: {
                        'name': 'test_action_1',
                        'enabled': False
                    }
                }
            }
        }]
        test_session = mock.MagicMock(description=test_description)

        with self.assertRaisesRegex(ValueError,
                                    'Cannot execute disabled action'):
            actions.ActionServices.execute(test_action_id, test_session,
                                           None, None, None)

    def test_get_result(self):
        mock_task = mock.MagicMock(result='test_result')
        mock_unit = mock.MagicMock()
        mock_unit.query().filter_by().first.return_value = mock_task
        result = actions.ActionServices.get_result('eid', 'tid', mock_unit)
        self.assertEqual(mock_task.result, result)

        mock_unit.query().filter_by().first.return_value = None
        task = actions.ActionServices.get_result('eid', 'tid', mock_unit)
        self.assertIsNone(task)
        mock_unit.query().filter_by.assert_any_call(id='tid',
                                                    environment_id='eid')
