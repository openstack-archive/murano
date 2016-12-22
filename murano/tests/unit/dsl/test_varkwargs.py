# Copyright (c) 2015 Mirantis, Inc.
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

from yaql.language import exceptions as yaql_exceptions

from murano.dsl import exceptions as dsl_exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestVarKwArgs(test_case.DslTestCase):
    def setUp(self):
        super(TestVarKwArgs, self).setUp()
        self._runner = self.new_runner(om.Object('TestVarKwArgs'))

    def test_varargs(self):
        self.assertEqual([2, 3, 4], self._runner.testVarArgs())

    def test_kwargs(self):
        self.assertEqual({'arg2': 2, 'arg3': 3}, self._runner.testKwArgs())

    def test_duplicate_kwargs(self):
        self.assertRaises(
            yaql_exceptions.NoMatchingMethodException,
            self._runner.testDuplicateKwArgs)

    def test_duplicate_varargs(self):
        self.assertRaises(
            yaql_exceptions.NoMatchingMethodException,
            self._runner.testDuplicateVarArgs)

    def test_explicit_varargs(self):
        self.assertRaises(
            yaql_exceptions.NoMatchingMethodException,
            self._runner.testExplicitVarArgs)

    def test_args(self):
        self.assertEqual(
            [[1, 2, 3], {'arg1': 4, 'arg2': 5, 'arg3': 6}],
            self._runner.testArgs())

    def test_varargs_contract(self):
        self.assertRaises(
            dsl_exceptions.ContractViolationException,
            self._runner.testVarArgsContract)

    def test_kwargs_contract(self):
        self.assertRaises(
            dsl_exceptions.ContractViolationException,
            self._runner.testKwArgsContract)
