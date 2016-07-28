# Copyright (c) 2015 OpenStack Foundation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

import murano.policy.modify.actions.default_actions as da
import murano.tests.unit.dsl.foundation.object_model as om
import murano.tests.unit.dsl.foundation.test_case as tc


class ModifyActionTestCase(tc.DslTestCase):
    def setUp(self):
        super(ModifyActionTestCase, self).setUp()
        self._list_member = om.Object('SampleClass2', class2Property='string2')
        self._dict_member = om.Object('SampleClass2', class2Property='string2')
        self._runner = self.new_runner(
            om.Object(
                'ModelExamples',
                sampleClass=om.Object(
                    'SampleClass1',
                    stringProperty='string1',
                    dictProperty={1: 'a', 2: 'b'},
                    dictClassProperty={
                        'key': self._dict_member},
                    classProperty=[self._list_member])))
        self._obj = self._runner.root


class TestRemoveObjectAction(ModifyActionTestCase):
    def test_remove(self):
        with self._runner.session():
            self.assertIsNotNone(self._obj.get_property('sampleClass'))
            object_id = self._obj.get_property('sampleClass').object_id
            da.RemoveObjectAction(object_id=object_id).modify(self._obj)
            self.assertIsNone(self._obj.get_property('sampleClass'))

    def test_remove_from_list(self):
        with self._runner.session():
            self.assertEqual(1, len(
                self._obj.get_property('sampleClass')
                    .get_property('classProperty')))
            da.RemoveObjectAction(object_id=self._list_member.id).modify(
                self._obj)
            self.assertEqual(0, len(
                self._obj.get_property('sampleClass')
                    .get_property('classProperty')))
            self.assertNotIn(self._list_member.id, repr(self._obj))

    def test_remove_from_dict(self):
        with self._runner.session():
            self.assertEqual(1, len(
                self._obj.get_property('sampleClass')
                    .get_property('dictClassProperty')))
            da.RemoveObjectAction(object_id=self._dict_member.id).modify(
                self._obj)
            self.assertEqual(0, len(
                self._obj.get_property('sampleClass')
                    .get_property('dictClassProperty')))
            self.assertNotIn(self._dict_member.id, repr(self._obj))

    def test_remove_not_exists(self):
        with self._runner.session():
            action = da.RemoveObjectAction(object_id='not_exists')
            self.assertRaises(ValueError, action.modify, self._obj)


class TestSetPropertyAction(ModifyActionTestCase):
    def test_set_str(self):
        self._test_set_value('stringProperty', 'test_string', 'test_string')

    def test_set_number(self):
        self._test_set_value('numberProperty', '15', 15)
        self._test_set_value('numberProperty', '50', 50)
        self._test_set_value('numberProperty', 40, 40)
        self._test_set_value('numberProperty', '-5', -5)

    def test_set_boolean(self):
        self._test_set_value('boolProperty', True, True)
        self._test_set_value('boolProperty', False, False)

    def test_set_dict(self):
        self._test_set_value('dictProperty', {1: 'a'}, {1: 'a'})
        self._test_set_value('dictProperty', {1: 'b', 2: 'c'},
                             {1: 'b', 2: 'c'})

    def _test_set_value(self, property, raw_input, expected):
        with self._runner.session():
            sample = self._obj.get_property('sampleClass')
            da.SetPropertyAction(sample.object_id, prop_name=property,
                                 value=raw_input).modify(self._obj)
            self.assertEqual(expected, sample.get_property(property))


class TestRemoveRelationAction(ModifyActionTestCase):
    def test_remove(self):
        with self._runner.session():
            self.assertIsNotNone(self._obj.get_property('sampleClass'))
            da.RemoveRelationAction(self._obj.object_id,
                                    prop_name='sampleClass').modify(self._obj)
            self.assertIsNone(self._obj.get_property('sampleClass'))


class TestAddRelationAction(ModifyActionTestCase):
    def test_add(self):
        with self._runner.session():
            sample = self._obj.get_property('sampleClass')
            self.assertIsNone(self._obj.get_property('anotherSampleClass'))
            da.AddRelationAction(source_id=self._obj.object_id,
                                 relation='anotherSampleClass',
                                 target_id=sample.object_id).modify(self._obj)
            self.assertIsNotNone(self._obj.get_property('anotherSampleClass'))
            rel_target = self._obj.get_property('anotherSampleClass').object_id
            self.assertEqual(sample.object_id, rel_target)


class TestAddObjectAction(ModifyActionTestCase):
    def test_add_object(self):
        with self._runner.session():
            self._obj.set_property('sampleClass', None)
            self.assertIsNone(self._obj.get_property('sampleClass'))
            da.AddObjectAction(
                self._obj.object_id,
                'sampleClass',
                'SampleClass1',
                {'stringProperty': 'test_add_obj'}).modify(self._obj)
            self.assertIsNotNone(self._obj.get_property('sampleClass'))
            self.assertEqual('test_add_obj',
                             self._obj.get_property('sampleClass')
                             .get_property('stringProperty'))
