# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

from murano.common import exceptions as exc
from murano.dsl import constants
from murano.dsl import helpers
from murano.dsl import yaql_integration
from murano.engine import execution_session
from murano.engine.system import agent
from murano.engine.system import agent_listener
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestAgentListener(test_case.DslTestCase):
    def setUp(self):
        super(TestAgentListener, self).setUp()

        # Register Agent class
        self.package_loader.load_package('io.murano', None).register_class(
            agent_listener.AgentListener)
        model = om.Object(
            'AgentListenerTests')
        self.runner = self.new_runner(model)
        self.context = yaql_integration.create_empty_context()
        self.context[constants.CTX_EXECUTION_SESSION] = \
            execution_session.ExecutionSession()

    def test_listener_enabled(self):
        self.override_config('disable_murano_agent', False, 'engine')
        al = self.runner.testAgentListener().extension
        self.assertTrue(al.enabled)
        with helpers.contextual(self.context):
            try:
                al.subscribe('msgid', 'event')
                self.assertEqual({'msgid': 'event'}, al._subscriptions)
            finally:
                al.stop()

    def test_listener_disabled(self):
        self.override_config('disable_murano_agent', True, 'engine')
        al = self.runner.testAgentListener().extension
        self.assertFalse(al.enabled)
        self.assertRaises(exc.PolicyViolationException,
                          al.subscribe, 'msgid', 'event')


class TestAgent(test_case.DslTestCase):
    def setUp(self):
        super(TestAgent, self).setUp()

        # Register Agent class
        self.package_loader.load_package('io.murano', None).register_class(
            agent.Agent)
        model = om.Object(
            'AgentTests')
        self.runner = self.new_runner(model)

    def test_agent_enabled(self):
        self.override_config('disable_murano_agent', False, 'engine')
        m = mock.MagicMock()
        # Necessary because otherwise there'll be an Environment lookup
        agent_cls = 'murano.engine.system.agent.Agent'
        obj_if_cls = 'murano.dsl.dsl.MuranoObjectInterface'
        with mock.patch(obj_if_cls + '.find_owner') as f:
            f.return_value = m
            a = self.runner.testAgent().extension
            self.assertTrue(a.enabled)
            self.assertEqual(m, a._environment)

            with mock.patch(agent_cls + '._send') as s:
                s.return_value = mock.MagicMock()
                a.send_raw({})
                s.assert_called_with({}, False, 0)

    def test_agent_disabled(self):
        self.override_config('disable_murano_agent', True, 'engine')
        a = self.runner.testAgent().extension
        self.assertFalse(a.enabled)
        self.assertRaises(exc.PolicyViolationException, a.call, {}, None)
        self.assertRaises(exc.PolicyViolationException, a.send, {}, None)
        self.assertRaises(exc.PolicyViolationException, a.call_raw, {})
        self.assertRaises(exc.PolicyViolationException, a.send_raw, {})
