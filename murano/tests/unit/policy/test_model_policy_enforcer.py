# Copyright (c) 2014 OpenStack Foundation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import congressclient
import mock

from murano.common import config
from murano.common import engine
from murano.engine import client_manager
from murano.policy import model_policy_enforcer
from murano.tests.unit import base


class TestModelPolicyEnforcer(base.MuranoTestCase):
    obj = mock.Mock()
    class_loader = mock.Mock()

    model_dict = mock.Mock()
    obj.to_dictionary = mock.Mock(return_value=model_dict)

    task = {
        'action': {'method': 'deploy'},
        'model': {'Objects': None},
        'token': 'token',
        'tenant_id': 'environment.tenant_id',
        'id': 'environment.id'
    }

    def setUp(self):
        super(TestModelPolicyEnforcer, self).setUp()
        self.congress_client_mock = \
            mock.Mock(spec=congressclient.v1.client.Client)

        self.client_manager_mock = mock.Mock(spec=client_manager.ClientManager)

        self.client_manager_mock.get_congress_client.return_value = \
            self.congress_client_mock

        self.environment = mock.Mock()
        self.environment.clients = self.client_manager_mock

    def test_enforcer_disabled(self):
        executor = engine.TaskExecutor(self.task)
        executor._model_policy_enforcer = mock.Mock()

        config.CONF.engine.enable_model_policy_enforcer = False
        executor._validate_model(self.obj, self.task['action'],
                                 self.class_loader)

        self.assertFalse(executor._model_policy_enforcer.validate.called)

    def test_enforcer_enabled(self):
        executor = engine.TaskExecutor(self.task)
        executor._model_policy_enforcer = mock.Mock()

        config.CONF.engine.enable_model_policy_enforcer = True
        executor._validate_model(self.obj, self.task['action'],
                                 self.class_loader)

        executor._model_policy_enforcer \
            .validate.assert_called_once_with(self.model_dict,
                                              self.class_loader)

    def test_validation_pass(self):
        self.congress_client_mock.execute_policy_action.return_value = \
            {"result": []}
        model = {'?': {'id': '123', 'type': 'class'}}
        enforcer = model_policy_enforcer.ModelPolicyEnforcer(self.environment)
        enforcer.validate(model)

    def test_validation_failure(self):
        self.congress_client_mock.execute_policy_action.return_value = \
            {"result": ['predeploy_errors("123","instance1","failure")']}

        model = {'?': {'id': '123', 'type': 'class'}}
        enforcer = model_policy_enforcer.ModelPolicyEnforcer(self.environment)
        self.assertRaises(model_policy_enforcer.ValidationError,
                          enforcer.validate, model)

    def test_parse_result(self):
        congress_response = [
            'unexpected response',
            'predeploy_errors("env1","instance1","Instance 1 has problem")',
            'predeploy_errors("env1","instance1","Instance 2 has problem")',
            'predeploy_errors("env2","instance1","Instance 3 has problem")'
        ]

        enforcer = model_policy_enforcer.ModelPolicyEnforcer(self.environment)
        result = enforcer._parse_messages('env1', congress_response)
        print result

        self.assertFalse("unexpected response" in result)
        self.assertTrue("Instance 1 has problem" in result)
        self.assertTrue("Instance 2 has problem" in result)
        self.assertFalse("Instance 3 has problem" in result)

    def test_action_not_deploy(self):
        executor = engine.TaskExecutor(self.task)
        executor._model_policy_enforcer = mock.Mock()

        config.CONF.engine.enable_model_policy_enforcer = True
        executor._validate_model(self.obj, {'method': 'not_deploy'},
                                 self.class_loader)

        self.assertFalse(executor._model_policy_enforcer.validate.called)
