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


class TestMultipleInheritance(test_case.DslTestCase):
    def setUp(self):
        super(TestMultipleInheritance, self).setUp()
        self._multi_derived = om.Object(
            'DerivedFrom2Classes',
            rootProperty='ROOT')
        model = om.Object(
            'SampleClass3',
            multiClassProperty=self._multi_derived
        )
        self._runner = self.new_runner(model)

    def test_multi_class_contract(self):
        self._runner.testMultiContract()
        self.assertEqual(
            ['ParentClass1::method1', 'ParentClass2::method2'],
            self.traces)

    def test_root_method_resolution(self):
        self._runner.on(self._multi_derived).testRootMethod()
        self.assertEqual(
            ['CommonParent::testRootMethod', 'ROOT'],
            self.traces)

    def test_property_accessible_on_several_paths(self):
        self.assertEqual(
            'ROOT',
            self._runner.testPropertyAccessibleOnSeveralPaths())

    def test_specialized_mixin_override(self):
        self._runner.on(self._multi_derived).testMixinOverride()
        self.assertEqual(
            ['ParentClass2::virtualMethod', '-',
             'CommonParent::virtualMethod', '-',
             'CommonParent::virtualMethod', '-',
             'ParentClass2::virtualMethod'],
            self.traces)

    def test_super(self):
        self._runner.on(self._multi_derived).testSuper()
        self.assertItemsEqual(
            ['CommonParent::virtualMethod', 'ParentClass2::virtualMethod',
             'CommonParent::virtualMethod', 'ParentClass2::virtualMethod'],
            self.traces)

    def test_psuper(self):
        self._runner.on(self._multi_derived).testPsuper()
        self.assertItemsEqual(
            ['CommonParent::virtualMethod', 'ParentClass2::virtualMethod',
             'CommonParent::virtualMethod', 'ParentClass2::virtualMethod'],
            self.traces)
