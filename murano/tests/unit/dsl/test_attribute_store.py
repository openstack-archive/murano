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
import mock

from murano.dsl import attribute_store
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.tests.unit.dsl.foundation import test_case


class TestAttributeStore(test_case.DslTestCase):
    def setUp(self):
        super(TestAttributeStore, self).setUp()
        self.attribute_store = attribute_store.AttributeStore()
        self.fake_object = mock.MagicMock(object_id=mock.sentinel.oid)
        self.tagged_obj = dsl.MuranoObjectInterface(self.fake_object)
        self.owner_type = dsl_types.MuranoTypeReference(self.fake_object)
        self.owner_type.type.name = mock.sentinel.typename
        self.name = 'foobar'

    def test_get_attribute_key(self):
        oid, typename = mock.sentinel.oid, mock.sentinel.typename

        key = self.attribute_store._get_attribute_key(
            self.tagged_obj, self.owner_type, self.name)
        expected_key = (oid, (typename, 'foobar'))

        self.assertEqual(expected_key, key)

    @mock.patch.object(attribute_store.AttributeStore, '_get_attribute_key',
                       return_value=(mock.sentinel.key1, mock.sentinel.key2))
    def test_get(self, mock_get_attr_key):
        key1, key2 = mock.sentinel.key1, mock.sentinel.key2
        get_val = mock.sentinel.get_val

        self.attribute_store._attributes = mock.MagicMock()
        self.attribute_store._attributes[key1].get.return_value = get_val
        val = self.attribute_store.get(
            self.tagged_obj, self.owner_type, self.name)

        mock_get_attr_key.assert_called_with(
            self.tagged_obj, self.owner_type, self.name)
        self.attribute_store._attributes[key1].get.assert_called_with(key2)
        self.assertEqual(get_val, val)

    @mock.patch.object(attribute_store.AttributeStore, '_get_attribute_key',
                       return_value=(mock.sentinel.key1, mock.sentinel.key2))
    def test_set_object_if(self, mock_get_attr_key):
        val = dsl.MuranoObjectInterface(self.fake_object)
        self.attribute_store._attributes = mock.MagicMock()
        self.attribute_store.set(
            self.tagged_obj, self.owner_type, self.name, val)

    @mock.patch.object(attribute_store.AttributeStore, '_get_attribute_key',
                       return_value=(mock.sentinel.key1, mock.sentinel.key2))
    def test_set_object(self, mock_get_attr_key):
        key1, key2 = mock.sentinel.key1, mock.sentinel.key2

        val = dsl_types.MuranoObject()
        val.object_id = mock.sentinel.oid
        self.attribute_store.set(
            self.tagged_obj, self.owner_type, self.name, val)
        self.assertEqual(self.attribute_store._attributes[key1][key2],
                         mock.sentinel.oid)

    @mock.patch.object(attribute_store.AttributeStore, '_get_attribute_key',
                       return_value=(mock.sentinel.key1, mock.sentinel.key2))
    def test_set_none(self, mock_get_attr_key):
        key1, key2 = mock.sentinel.key1, mock.sentinel.key2

        val = None
        self.attribute_store._attributes = mock.MagicMock()
        self.attribute_store.set(
            self.tagged_obj, self.owner_type, self.name, val)

        self.attribute_store._attributes[key1].pop.assert_called_with(
            key2, None)

    def test_serialize(self):
        known_objects = ['obj1', 'obj3']
        self.attribute_store._attributes = {
            'obj1': {
                ('foo', 'obj11'): 11,
                ('bar', 'obj12'): 12
            },
            'obj2': {
                ('baz', 'obj21'): 21
            },
            'obj3': {
                ('foobar', 'obj31'): 31
            }
        }
        val = self.attribute_store.serialize(known_objects)
        expected = [
            ['obj1', 'foo', 'obj11', 11],
            ['obj1', 'bar', 'obj12', 12],
            ['obj3', 'foobar', 'obj31', 31]]

        self.assertEqual(sorted(expected), sorted(val))

    def test_load(self):
        data = [
            ['a', 'b', 'c', 'd'],
            ['a', 'f', 'g', None],
            ['b', 'i', 'j', 'k']
        ]

        self.attribute_store.load(data)
        expected = {'a': {('b', 'c'): 'd'},
                    'b': {('i', 'j'): 'k'}}
        self.assertEqual(expected, self.attribute_store._attributes)

    def test_forget_object_if(self):
        obj = dsl.MuranoObjectInterface(mock.MagicMock(object_id='bar'))
        self.attribute_store._attributes = {'foo': 42, 'bar': 43}
        self.attribute_store.forget_object(obj)
        self.assertEqual({'foo': 42}, self.attribute_store._attributes)

    def test_forget_object(self):
        obj = dsl_types.MuranoObject()
        obj.object_id = 'foo'
        self.attribute_store._attributes = {'foo': 42, 'bar': 43}
        self.attribute_store.forget_object(obj)
        self.assertEqual({'bar': 43}, self.attribute_store._attributes)
