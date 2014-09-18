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

from murano.dsl import exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestPropertyInitialization(test_case.DslTestCase):
    def setUp(self):
        super(TestPropertyInitialization, self).setUp()
        model = om.Object(
            'PropertyInit'
        )
        self._runner = self.new_runner(model)

    def test_runtime_property_default(self):
        self.assertEqual(
            'DEFAULT',
            self._runner.testRuntimePropertyDefault())

    def test_runtime_property_without_default(self):
        self.assertRaises(
            exceptions.UninitializedPropertyAccessError,
            self._runner.testRuntimePropertyWithoutDefault)

    def test_runtime_property_with_strict_contract_without_default(self):
        self.assertEqual(
            'VALUE',
            self._runner.testRuntimePropertyWithStrictContractWithoutDefault())

    def test_uninitialized_runtime_property_with_strict_contract(self):
        self.assertRaises(
            exceptions.UninitializedPropertyAccessError,
            self._runner.testUninitializedRuntimeProperty)
