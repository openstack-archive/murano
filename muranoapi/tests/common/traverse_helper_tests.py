#    Copyright (c) 2013 Mirantis, Inc.
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

import unittest2 as unittest
from muranoapi.common.utils import TraverseHelper


class TraverseHelperTests(unittest.TestCase):
    def test_root_get_with_dict(self):
        source = {'attr': True}
        value = TraverseHelper.get('/', source)
        self.assertDictEqual(value, source)

    def test_root_get_with_list(self):
        source = [{'attr': True}]
        value = TraverseHelper.get('/', source)
        self.assertListEqual(value, source)

    def test_root_get_with_value_type(self):
        source = 'source'
        value = TraverseHelper.get('/', source)
        self.assertEqual(value, source)

    def test_attribute_get(self):
        source = {'attr': True}
        value = TraverseHelper.get('/attr', source)
        self.assertEqual(value, True)

    def test_nested_attribute_get(self):
        source = {'obj': {'attr': True}}
        value = TraverseHelper.get('/obj/attr', source)
        self.assertEqual(value, True)

    def test_list_item_attribute_get(self):
        source = {'obj': [
            {'id': '1', 'value': 1},
            {'id': '2s', 'value': 2},
        ]}
        value = TraverseHelper.get('/obj/2s/value', source)
        self.assertEqual(value, 2)

    def test_list_item_attribute_get_by_index(self):
        source = {'obj': [
            {'id': 'guid1', 'value': 1},
            {'id': 'guid2', 'value': 2},
        ]}
        value = TraverseHelper.get('/obj/1/value', source)
        self.assertEqual(value, 2)

    def test_attribute_set(self):
        source = {'attr': True}
        TraverseHelper.update('/newAttr', False, source)
        value = TraverseHelper.get('/newAttr', source)
        self.assertEqual(value, False)

    def test_attribute_update(self):
        source = {'attr': True}
        TraverseHelper.update('/attr', False, source)
        value = TraverseHelper.get('/attr', source)
        self.assertEqual(value, False)

    def test_nested_attribute_update(self):
        source = {'obj': {'attr': True}}
        TraverseHelper.update('/obj/attr', False, source)
        value = TraverseHelper.get('/obj/attr', source)
        self.assertEqual(value, False)

    def test_adding_item_to_list(self):
        source = {'attr': [1, 2, 3]}
        TraverseHelper.insert('/attr', 4, source)
        value = TraverseHelper.get('/attr', source)
        self.assertListEqual(value, [1, 2, 3, 4])

    def test_nested_adding_item_to_list(self):
        source = {'obj': {'attr': [1, 2, 3]}}
        TraverseHelper.insert('/obj/attr', 4, source)
        value = TraverseHelper.get('/obj/attr', source)
        self.assertListEqual(value, [1, 2, 3, 4])

    def test_attribute_remove_from_dict(self):
        source = {'attr1': False, 'attr2': True}
        TraverseHelper.remove('/attr1', source)
        value = TraverseHelper.get('/', source)
        self.assertDictEqual(value, {'attr2': True})

    def test_nested_attribute_remove_from_dict(self):
        source = {'obj': {'attr1': False, 'attr2': True}}
        TraverseHelper.remove('/obj/attr1', source)
        value = TraverseHelper.get('/obj', source)
        self.assertDictEqual(value, {'attr2': True})

    def test_nested_attribute_remove_from_list_by_id(self):
        source = {'obj': [{'id': 'id1'}, {'id': 'id2'}]}
        TraverseHelper.remove('/obj/id1', source)
        value = TraverseHelper.get('/obj', source)
        self.assertListEqual(value, [{'id': 'id2'}])

    def test_nested_attribute_remove_from_list_by_index(self):
        source = {'obj': [{'id': 'id1'}, {'id': 'id2'}]}
        TraverseHelper.remove('/obj/0', source)
        value = TraverseHelper.get('/obj', source)
        self.assertListEqual(value, [{'id': 'id2'}])
