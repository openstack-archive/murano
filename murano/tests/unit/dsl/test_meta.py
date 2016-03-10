# Copyright (c) 2016 Mirantis, Inc.
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


class TestMeta(test_case.DslTestCase):
    def setUp(self):
        super(TestMeta, self).setUp()
        self._runner = self.new_runner(om.Object('metatests.TestMeta'))

    def test_class_multi_meta(self):
        self.assertItemsEqual(
            [4, 1, 111, 2], self._runner.testClassMultiMeta())

    def test_class_single_meta(self):
        self.assertItemsEqual(
            [5, 6], self._runner.testClassSingleMeta())

    def test_parent_class_not_inherited_meta(self):
        self.assertEqual(3, self._runner.testParentClassNotInheritedMeta())

    def test_method_meta(self):
        self.assertItemsEqual(
            [7, 8, 9, 4, 1, 10], self._runner.testMethodMeta())

    def test_method_argument_meta(self):
        self.assertItemsEqual(
            [1, 2, 3], self._runner.testMethodArgumentMeta())

    def test_inherited_property_meta(self):
        self.assertEqual(
            [1], self._runner.testInheritedPropertyMeta())

    def test_overridden_property_meta(self):
        self.assertItemsEqual(
            [1, 4], self._runner.testOverriddenPropertyMeta())

    def test_package_meta(self):
        self.assertEqual(
            [], self._runner.testPackageMeta())

    def test_complex_meta(self):
        self.assertItemsEqual([
            [1, 'metatests.PropertyType'],
            [2, 'metatests.PropertyType'],
            [3, 'metatests.PropertyType2'],
            [4, 'metatests.PropertyType'],
            [5, 'metatests.PropertyType2']
        ], self._runner.testComplexMeta())
