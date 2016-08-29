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


class TestPropertyAccess(test_case.DslTestCase):
    def setUp(self):
        super(TestPropertyAccess, self).setUp()
        self._multi_derived = om.Object(
            'DerivedFrom2Classes',
            rootProperty='ROOT',
            ambiguousProperty=321)
        model = om.Object(
            'SampleClass3',
            multiClassProperty=self._multi_derived
        )
        self._runner = self.new_runner(model)

    def test_private_property_access(self):
        self.assertIsNone(self._runner.testPrivateProperty())
        self.assertEqual(
            ['CommonParent', 'ParentClass1', 'SampleClass3'],
            self.traces)

    def test_private_property_access_failure(self):
        e = self.assertRaises(
            exceptions.UninitializedPropertyAccessError,
            self._runner.testUninitializedPrivatePropertyAccess)
        self.assertEqual(
            'Access to uninitialized property "privateName" '
            'in class "SampleClass3" is forbidden', str(e))

    def test_read_of_private_property_of_other_class(self):
        e = self.assertRaises(
            exceptions.PropertyAccessError,
            self._runner.testReadOfPrivatePropertyOfOtherClass)
        self.assertEqual(
            'Property "privateProperty" in class "DerivedFrom2Classes" '
            'cannot be read', str(e))
        self.assertEqual(['accessing property'], self.traces)

    def test_write_of_private_property_of_other_class(self):
        e = self.assertRaises(
            exceptions.PropertyAccessError,
            self._runner.testWriteOfPrivatePropertyOfOtherClass)
        self.assertEqual(
            'Property "privateProperty" in class "DerivedFrom2Classes" '
            'cannot be written', str(e))

    def test_access_ambiguous_property_with_resolver(self):
        self.assertEqual(
            '321',
            self._runner.on(self._multi_derived).
            testAccessAmbiguousPropertyWithResolver())

    def test_property_merge(self):
        self.assertEqual(
            '555',
            self._runner.on(self._multi_derived).
            testPropertyMerge())
        self.assertEqual(
            ['321', '555', '555', '555', '555'],
            self.traces)

    def test_property_usage(self):
        e = self.assertRaises(
            exceptions.NoWriteAccessError,
            self._runner.on(self._multi_derived).
            testModifyUsageTestProperty1)
        self.assertEqual(
            'Property "usageTestProperty1" is immutable to the caller',
            str(e))
        self.assertRaises(
            exceptions.NoWriteAccessError,
            self._runner.on(self._multi_derived).
            testModifyUsageTestProperty2)
        self.assertEqual(
            33,
            self._runner.on(self._multi_derived).
            testModifyUsageTestProperty3())
        self.assertEqual(
            44,
            self._runner.on(self._multi_derived).
            testModifyUsageTestProperty4())
        self.assertEqual(
            55,
            self._runner.on(self._multi_derived).
            testModifyUsageTestProperty5())
        self.assertRaises(
            exceptions.NoWriteAccessError,
            self._runner.on(self._multi_derived).
            testModifyUsageTestProperty6)
        self.assertEqual(
            77,
            self._runner.on(
                self._multi_derived).testModifyUsageTestProperty7())
