# Copyright (c) 2016 Mirantis, Inc.
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
from oslo_messaging.rpc import client
from oslo_serialization import jsonutils
from webob import exc

from murano.api.v1 import static_actions
from murano.common import policy
import murano.tests.unit.api.base as tb


@mock.patch.object(policy, 'check')
class TestStaticActionsApi(tb.ControllerTest, tb.MuranoApiTestCase):

    def setUp(self):
        super(TestStaticActionsApi, self).setUp()
        self.controller = static_actions.Controller()

    def test_execute_static_action(self, mock_policy_check):
        """Test that action execution results in the correct rpc call."""
        self._set_policy_rules(
            {'execute_action': '@'}
        )

        action = {
            'method': 'TestAction',
            'args': {'name': 'John'},
            'class_name': 'TestClass',
            'pkg_name': 'TestPackage',
            'class_version': '=0'
        }
        rpc_task = {
            'action': action,
            'token': None,
            'project_id': 'test_tenant',
            'user_id': 'test_user',
            'id': mock.ANY
        }

        request_data = {
            "className": 'TestClass',
            "methodName": 'TestAction',
            "packageName": 'TestPackage',
            "classVersion": '=0',
            "parameters": {'name': 'John'}
        }
        req = self._post('/actions', jsonutils.dump_as_bytes(request_data))
        try:
            self.controller.execute(req, request_data)
        except TypeError:
            pass
        self.mock_engine_rpc.call_static_action.assert_called_once_with(
            rpc_task)

    def test_execute_static_action_handle_bad_data_exc(self, _):
        request_data = {
            "className": None,
            "methodName": 'TestAction'
        }
        req = self._post('/actions', jsonutils.dump_as_bytes(request_data))
        self.assertRaises(exc.HTTPBadRequest, self.controller.execute, req,
                          request_data)

        request_data = {
            "className": 'TestClass',
            "methodName": None
        }
        req = self._post('/actions', jsonutils.dump_as_bytes(request_data))
        self.assertRaises(exc.HTTPBadRequest, self.controller.execute, req,
                          request_data)

    @mock.patch('murano.services.static_actions.StaticActionServices.execute')
    def test_execute_static_action_handle_execute_excs(self, mock_execute, _):
        """Test whether execute handles all exceptions thrown correctly."""
        request_data = {
            "className": 'TestClass',
            "methodName": 'TestAction',
            "packageName": 'TestPackage',
            "classVersion": '=0',
            "parameters": {'name': 'John'}
        }

        exc_types = ['NoClassFound', 'NoMethodFound',
                     'NoPackageFound', 'NoPackageForClassFound',
                     'MethodNotExposed', 'NoMatchingMethodException']
        for exc_type in exc_types:
            mock_execute.side_effect = client.RemoteError(exc_type=exc_type)
            req = self._post('/actions', jsonutils.dump_as_bytes(request_data))
            self.assertRaises(exc.HTTPNotFound, self.controller.execute, req,
                              request_data)
        self.assertEqual(mock_execute.call_count, len(exc_types))

        exc_type = 'ContractViolationException'
        mock_execute.side_effect = client.RemoteError(exc_type=exc_type)
        req = self._post('/actions', jsonutils.dump_as_bytes(request_data))
        self.assertRaises(exc.HTTPBadRequest, self.controller.execute, req,
                          request_data)
        exc_types.append(exc_type)
        self.assertEqual(mock_execute.call_count, len(exc_types))

        exc_type = 'ThisIsARandomTestException'
        mock_execute.side_effect = client.RemoteError(exc_type=exc_type)
        req = self._post('/actions', jsonutils.dump_as_bytes(request_data))
        self.assertRaises(exc.HTTPServiceUnavailable, self.controller.execute,
                          req, request_data)
        exc_types.append(exc_type)
        self.assertEqual(mock_execute.call_count, len(exc_types))

        try:
            int('this will throw a value error')
        except ValueError as e:
            setattr(e, 'message', None)
            exc_type = e
        mock_execute.side_effect = exc_type
        req = self._post('/actions', jsonutils.dump_as_bytes(request_data))
        self.assertRaises(exc.HTTPBadRequest, self.controller.execute,
                          req, request_data)
        exc_types.append(exc_type)
        self.assertEqual(mock_execute.call_count, len(exc_types))
