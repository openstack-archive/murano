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
from oslo_config import cfg

from murano.common import engine
from murano.policy import model_policy_enforcer
from murano.tests.unit import base

CONF = cfg.CONF


class TestModelPolicyEnforcer(base.MuranoTestCase):
    def setUp(self):
        super(TestModelPolicyEnforcer, self).setUp()

        self.obj = mock.Mock()
        self.package_loader = mock.Mock()

        self.model_dict = mock.Mock()
        self.obj.to_dictionary = mock.Mock(return_value=self.model_dict)

        self.task = {
            'action': {'method': 'deploy'},
            'model': {'Objects': None},
            'token': 'token',
            'tenant_id': 'environment.tenant_id',
            'id': 'environment.id'
        }

        self.congress_client_mock = \
            mock.Mock(spec=congressclient.v1.client.Client)
        model_policy_enforcer.ModelPolicyEnforcer._create_client = mock.Mock(
            return_value=self.congress_client_mock)

    def test_enforcer_disabled(self):
        executor = engine.TaskExecutor(self.task)
        executor._model_policy_enforcer = mock.Mock()

        CONF.engine.enable_model_policy_enforcer = False
        executor._validate_model(self.obj, self.package_loader)

        self.assertFalse(executor._model_policy_enforcer.validate.called)

    def test_enforcer_enabled(self):
        executor = engine.TaskExecutor(self.task)
        executor._model_policy_enforcer = mock.Mock()

        CONF.engine.enable_model_policy_enforcer = True
        executor._validate_model(self.obj, self.package_loader)

        executor._model_policy_enforcer \
            .validate.assert_called_once_with(self.model_dict,
                                              self.package_loader)

    def test_validation_pass(self):
        self.congress_client_mock.execute_policy_action.return_value = \
            {"result": []}
        model = {'?': {'id': '123', 'type': 'class'}}
        enforcer = model_policy_enforcer.ModelPolicyEnforcer(mock.Mock())
        enforcer.validate(model)

    def test_validation_failure(self):
        self.congress_client_mock.execute_policy_action.return_value = \
            {"result": ['predeploy_errors("123","instance1","failure")']}

        model = {'?': {'id': '123', 'type': 'class'}}
        enforcer = model_policy_enforcer.ModelPolicyEnforcer(mock.Mock())
        self.assertRaises(model_policy_enforcer.ValidationError,
                          enforcer.validate, model)

    def test_modify(self):
        model = {'?': {'id': '123', 'type': 'class'}}
        obj = mock.MagicMock()
        obj.to_dictionary = mock.Mock(return_value=model)
        self.congress_client_mock.execute_policy_action.return_value = \
            {"result": [
                'predeploy_modify("123","instance1",'
                '"remove-object: {object_id: "12"}")']}

        action_manager = mock.MagicMock()
        enforcer = model_policy_enforcer.ModelPolicyEnforcer(
            mock.Mock(), action_manager)

        enforcer.modify(obj)
        self.assertTrue(action_manager.apply_action.called)

    def test_parse_result(self):
        congress_response = [
            'unexpected response',
            'predeploy_errors("env1","instance1","Instance 1 has problem")',
            'predeploy_errors("env1","instance1","Instance 2 has problem")',
            'predeploy_errors("env2","instance1","Instance 3 has problem")'
        ]

        enforcer = model_policy_enforcer.ModelPolicyEnforcer(None)
        result = enforcer._parse_simulation_result(
            'predeploy_errors', 'env1', congress_response)

        self.assertFalse("unexpected response" in result)
        self.assertTrue("Instance 1 has problem" in result)
        self.assertTrue("Instance 2 has problem" in result)
        self.assertFalse("Instance 3 has problem" in result)

    def test_none_model(self):
        executor = engine.TaskExecutor(self.task)
        executor._model_policy_enforcer = mock.Mock()

        CONF.engine.enable_model_policy_enforcer = True

        executor._validate_model(None, self.package_loader)

        self.assertFalse(executor._model_policy_enforcer.modify.called)
        self.assertFalse(executor._model_policy_enforcer.validate.called)

        executor._validate_model(self.obj, self.package_loader)

        self.assertTrue(executor._model_policy_enforcer.modify.called)
        self.assertTrue(executor._model_policy_enforcer.validate.called)
