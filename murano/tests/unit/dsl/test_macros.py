# Copyright (c) 2014 Mirantis, Inc.
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


from testtools import matchers

from murano.dsl import exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestMacros(test_case.DslTestCase):
    def setUp(self):
        super(TestMacros, self).setUp()
        self._runner = self.new_runner(om.Object('MacroExamples'))

    def test_if(self):
        self.assertEqual('gt', self._runner.testIf(6))
        self.assertEqual('def', self._runner.testIf(4))
        self.assertEqual('gt', self._runner.testIfElse(6))
        self.assertEqual('lt', self._runner.testIfElse(4))

    def test_if_non_boolean(self):
        self.assertEqual(1100, self._runner.testIfNonBoolean())

    def test_while(self):
        self.assertEqual(0, self._runner.testWhile(3))
        self.assertEqual([3, 2, 1], self.traces)

    def test_while_non_boolean(self):
        self.assertEqual([], self._runner.testWhileNonBoolean())

    def test_for(self):
        self.assertIsNone(self._runner.testFor())
        self.assertEqual(['x', 'y', 'z', 2, 5, 10], self.traces)

    def test_repeat(self):
        self._runner.testRepeat(4)
        self.assertEqual(['run', 'run', 'run', 'run'], self.traces)

    def test_break(self):
        self.assertRaises(exceptions.DslInvalidOperationError,
                          self._runner.testBreak)
        self.assertEqual([0, 1, 2, 'breaking', 'method_break'], self.traces)

    def test_continue(self):
        self.assertRaises(exceptions.DslInvalidOperationError,
                          self._runner.testContinue)
        self.assertEqual([0, 1, 2, 5, 6, 'method_continue'], self.traces)

    def test_match(self):
        self.assertEqual('y', self._runner.testMatch(1))
        self.assertEqual('x', self._runner.testMatch(2))
        self.assertEqual('z', self._runner.testMatch(3))
        self.assertIsNone(self._runner.testMatch(0))
        self.assertEqual('y', self._runner.testMatchDefault(1))
        self.assertEqual('x', self._runner.testMatchDefault(2))
        self.assertEqual('z', self._runner.testMatchDefault(3))
        self.assertEqual('def', self._runner.testMatchDefault(0))

    def test_switch(self):
        self.assertIsNone(self._runner.testSwitch(20))
        self.assertEqual(['gt'], self.traces)
        del self.traces
        self.assertIsNone(self._runner.testSwitch(200))
        self.assertThat(
            self.traces,
            matchers.MatchesSetwise(
                matchers.Equals('gt100'), matchers.Equals('gt')))
        del self.traces
        self.assertIsNone(self._runner.testSwitch(2))
        self.assertEqual(['lt'], self.traces)

    def test_switch_with_default(self):
        self.assertIsNone(self._runner.testSwitchDefault(20))
        self.assertEqual(['gt'], self.traces)
        del self.traces
        self.assertIsNone(self._runner.testSwitchDefault(200))
        self.assertThat(
            self.traces,
            matchers.MatchesSetwise(
                matchers.Equals('gt100'), matchers.Equals('gt')))
        del self.traces
        self.assertIsNone(self._runner.testSwitchDefault(-20))
        self.assertEqual(['lt'], self.traces)
        del self.traces
        self.assertIsNone(self._runner.testSwitchDefault(5))
        self.assertEqual(['def'], self.traces)

    def test_switch_non_boolean(self):
        self.assertEqual(1110000, self._runner.testSwitchNonBoolean())

    def test_code_block(self):
        self.assertEqual(123, self._runner.testCodeBlock())
        self.assertEqual(['a', 123], self.traces)

    def test_parallel(self):
        self.assertIsNone(self._runner.testParallel())
        self.assertEqual(['enter', 'enter', 'exit', 'exit'], self.traces)

    def test_parallel_with_limit(self):
        self.assertIsNone(self._runner.testParallelWithLimit())
        self.assertEqual(['enter', 'enter',
                          'exit', 'exit',
                          'enter', 'exit'], self.traces)

    def test_scope_within_macro(self):
        self.assertEqual(
            87654321,
            self._runner.testScopeWithinMacro())
