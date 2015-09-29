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

from murano.dsl import dsl_exception
from murano.dsl import exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestExecution(test_case.DslTestCase):
    def _load(self):
        return self.new_runner(
            om.Object('SampleClass1', stringProperty='STRING',
                      classProperty=om.Object(
                          'SampleClass2', class2Property='ANOTHER_STRING')))

    def test_load(self):
        self._load()

    def test_load_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self.new_runner,
            om.Object('SampleClass1'))

    def test_trace(self):
        runner = self._load()
        self.assertEqual([], self.traces)
        runner.testTrace(123)
        self.assertEqual([123, 'STRING', 'ANOTHER_STRING'], self.traces)
        runner.testTrace(321)
        self.assertEqual([123, 'STRING', 'ANOTHER_STRING',
                          321, 'STRING', 'ANOTHER_STRING'],
                         self.traces)

    def test_exception(self):
        class CustomException(Exception):
            pass

        def raise_exception():
            raise CustomException()

        self.register_function(raise_exception, 'raiseException')
        runner = self._load()
        self.assertRaises(CustomException, runner.testException)
        runner.preserve_exception = True
        self.assertRaises(dsl_exception.MuranoPlException,
                          runner.testException)

    def test_return(self):
        self.assertEqual(3, self._load().testReturn(3))
