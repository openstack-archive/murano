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

from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestAssignments(test_case.DslTestCase):
    def setUp(self):
        super(TestAssignments, self).setUp()
        self._runner = self.new_runner(
            om.Object(
                'SampleClass1',
                stringProperty='string',
                classProperty=om.Object(
                    'SampleClass2',
                    class2Property='another string')))

    def test_assignment(self):
        self.assertEqual(
            {
                'Arr': [5, 2, [10, 123]],
                'Dict': {
                    'Key1': 'V1',
                    'Key2': {'KEY2': 'V3', 'a_b': 'V2'}
                }
            }, self._runner.testAssignment())

    def test_assignment_on_property(self):
        self.assertEqual(
            {
                'Arr': [5, 2, [10, 123]],
                'Dict': {
                    'Key1': 'V1',
                    'Key2': {'KEY2': 'V3', 'a_b': 'V2'}
                }
            }, self._runner.testAssignmentOnProperty())

    def test_assign_by_copy(self):
        self.assertEqual(
            [1, 2, 3],
            self._runner.testAssignByCopy([1, 2, 3]))
