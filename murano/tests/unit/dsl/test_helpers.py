# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import mock
import semantic_version
import weakref

from oslo_utils.uuidutils import generate_uuid

from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.tests.unit import base


class TestDSLHelpers(base.MuranoTestCase):
    @mock.patch.object(helpers, 'with_object_store', autospec=True)
    def test_parallel_select_except_exception(self, mock_with_object_store):
        mock_with_object_store.side_effect = ValueError
        self.assertRaises(ValueError, helpers.parallel_select,
                          [mock.sentinel.foo], lambda: None)

    def test_enum(self):
        self.assertEqual('Enum', helpers.enum().__name__)

    def test_cast_with_murano_type(self):
        mock_attrs = {
            'name': mock.sentinel.class_type,
            'version': semantic_version.Version('1.0.0'),
            'ancestors.return_value': []
        }
        mock_type = mock.Mock()
        mock_type.configure_mock(**mock_attrs)
        mock_obj = mock.Mock(type=mock_type)
        mock_obj.cast.return_value = mock.sentinel.foo_cast_value
        mock_murano_class = mock.Mock(spec=dsl_types.MuranoType)
        mock_murano_class.name = mock.sentinel.class_type
        mock_murano_class.version = semantic_version.Version('1.0.0')

        result = helpers.cast(mock_obj, mock_murano_class,
                              pov_or_version_spec=None)
        self.assertEqual(mock.sentinel.foo_cast_value, result)
        mock_obj.cast.assert_called_once_with(mock_type)

    def test_cast_except_value_error(self):
        mock_attrs = {
            'name': mock.sentinel.class_type,
            'version': semantic_version.Version('1.0.0'),
            'ancestors.return_value': []
        }
        mock_type = mock.Mock()
        mock_type.configure_mock(**mock_attrs)
        mock_obj = mock.Mock(type=mock_type)
        mock_murano_class = mock.Mock(spec=dsl_types.MuranoType)
        mock_murano_class.name = mock.sentinel.class_type

        e = self.assertRaises(ValueError, helpers.cast, mock_obj,
                              mock_murano_class,
                              pov_or_version_spec=mock.Mock())
        self.assertEqual('pov_or_version_spec of unsupported type {0}'
                         .format(type(mock.Mock())), str(e))

    def test_cast_except_no_class_found(self):
        mock_attrs = {
            'name': mock.sentinel.name,
            'package.name': mock.sentinel.package_name,
            'version': mock.sentinel.version,
            'ancestors.return_value': []
        }
        mock_type = mock.Mock()
        mock_type.configure_mock(**mock_attrs)
        mock_obj = mock.Mock(type=mock_type)
        mock_murano_class = mock.Mock(spec=dsl_types.MuranoTypeReference)
        mock_murano_class.type = mock.sentinel.foo_class
        mock_version_spec = mock.Mock(spec=dsl_types.MuranoPackage)

        e = self.assertRaises(exceptions.NoClassFound, helpers.cast, mock_obj,
                              mock_murano_class,
                              pov_or_version_spec=mock_version_spec)
        self.assertIn('Class "sentinel.foo_class" is not found', str(e))

    def test_cast_except_ambiguous_class_name(self):
        mock_attrs = {
            'name': mock.sentinel.class_type,
            'version': semantic_version.Version('1.0.0')
        }
        mock_ancestor = mock.Mock()
        mock_ancestor.configure_mock(**mock_attrs)
        mock_attrs['ancestors.return_value'] = [mock_ancestor]
        mock_type = mock.Mock()
        mock_type.configure_mock(**mock_attrs)
        mock_obj = mock.Mock(type=mock_type)
        mock_murano_class = mock.Mock(spec=dsl_types.MuranoTypeReference)
        mock_murano_class.type = mock.sentinel.class_type

        # pov_or_version_spec of '1' will be converted to
        # semantic_version.Spec('>=1.0.0,<2.0.0-0')
        self.assertRaises(exceptions.AmbiguousClassName, helpers.cast,
                          mock_obj, mock_murano_class, pov_or_version_spec='1')

    def test_inspect_is_method(self):
        mock_cls = mock.Mock(foo=lambda: None, bar=None)
        self.assertTrue(helpers.inspect_is_method(mock_cls, 'foo'))
        self.assertFalse(helpers.inspect_is_method(mock_cls, 'bar'))

    def test_inspect_is_property(self):
        data_descriptor = mock.MagicMock(__get__=None, __set__=None)
        mock_cls = mock.Mock(foo=data_descriptor, bar=None)
        self.assertTrue(helpers.inspect_is_property(mock_cls, 'foo'))
        self.assertFalse(helpers.inspect_is_property(mock_cls, 'bar'))

    def test_updated_dict(self):
        dict_ = {'foo': 'bar'}
        self.assertEqual(dict_, helpers.updated_dict(dict_, {}))

    def test_updated_dict_with_null_arg(self):
        dict_ = {'foo': 'bar'}
        self.assertEqual(dict_, helpers.updated_dict(None, dict_))

    def test_resolve_with_return_reference_true(self):
        mock_value = mock.Mock(spec=dsl_types.MuranoTypeReference)
        mock_scope_type = mock.Mock(spec=dsl_types.MuranoTypeReference)
        result = helpers.resolve_type(mock_value, mock_scope_type, True)
        self.assertEqual(mock_value, result)

        mock_value = mock.Mock()
        mock_value.get_reference.return_value = mock.sentinel.foo_reference
        mock_scope_type = mock.Mock()
        mock_scope_type.package.find_class.return_value = mock_value
        result = helpers.resolve_type(mock_value, mock_scope_type, True)
        self.assertEqual(mock.sentinel.foo_reference, result)

    def test_resolve_type_with_null_value(self):
        self.assertIsNone(helpers.resolve_type(None, None))

    def test_assemble_object_definition(self):
        test_parsed = {
            'type': mock.sentinel.type,
            'properties': {},
            'id': mock.sentinel.id,
            'name': mock.sentinel.name,
            'metadata': mock.sentinel.metadata,
            'destroyed': True,
            'extra': {}
        }
        expected = {
            '?': {
                'type': mock.sentinel.type,
                'id': mock.sentinel.id,
                'name': mock.sentinel.name,
                'metadata': mock.sentinel.metadata,
                'destroyed': True
            }
        }

        result = helpers.assemble_object_definition(test_parsed)
        for key, val in expected.items():
            self.assertEqual(val, result[key])

    @mock.patch.object(helpers, 'format_type_string', autospec=True)
    def test_assemble_object_definition_with_serializable_model_format(
            self, mock_format_type_string):
        mock_format_type_string.return_value = mock.sentinel.type

        test_parsed = {
            'type': mock.sentinel.type,
            'properties': {},
            'id': mock.sentinel.id,
            'name': mock.sentinel.name,
            'metadata': mock.sentinel.metadata,
            'destroyed': True,
            'extra': {}
        }
        expected = {
            '?': {
                'type': mock.sentinel.type,
                'id': mock.sentinel.id,
                'name': mock.sentinel.name,
                'metadata': mock.sentinel.metadata,
                'destroyed': True
            }
        }
        model_format = dsl_types.DumpTypes.Serializable

        result = helpers.assemble_object_definition(test_parsed, model_format)
        for key, val in expected['?'].items():
            self.assertEqual(val, result['?'][key])

    def test_assemble_object_definition_with_inline_model_format(self):
        test_parsed = {
            'type': mock.sentinel.type,
            'properties': mock.sentinel.properties,
            'id': mock.sentinel.id,
            'name': mock.sentinel.name,
            'metadata': mock.sentinel.metadata,
            'dependencies': mock.sentinel.dependencies,
            'destroyed': mock.sentinel.destroyed,
            'extra': {}
        }
        model_format = dsl_types.DumpTypes.Inline
        expected = copy.copy(test_parsed)
        expected[mock.sentinel.type] = mock.sentinel.properties
        for key in ['type', 'extra', 'properties']:
            expected.pop(key)

        result = helpers.assemble_object_definition(test_parsed, model_format)
        for key, val in expected.items():
            self.assertEqual(val, result[key])

    def test_assemble_object_definition_except_value_error(self):
        test_parsed = {
            'type': mock.sentinel.type,
            'properties': {},
            'id': mock.sentinel.id,
            'name': mock.sentinel.name,
            'metadata': mock.sentinel.metadata,
            'destroyed': True,
            'extra': {}
        }
        e = self.assertRaises(ValueError, helpers.assemble_object_definition,
                              test_parsed, None)
        self.assertEqual('Invalid Serialization Type', str(e))

    def test_weak_proxy(self):
        self.assertIsNone(helpers.weak_proxy(None))

    def test_weak_proxy_with_reference_type(self):
        result = helpers.weak_proxy(weakref.ReferenceType(int))
        self.assertEqual('int', result.__name__)

    @mock.patch.object(helpers, 'get_object_store', autospec=True)
    def test_weak_ref(self, mock_get_object_store):
        mock_object_store = mock.Mock(
            **{'get.return_value': mock.sentinel.res})
        mock_get_object_store.return_value = mock_object_store

        test_obj = dsl_types.MuranoObject()
        setattr(test_obj, 'object_id', generate_uuid())
        murano_object_weak_ref = helpers.weak_ref(test_obj)
        setattr(murano_object_weak_ref, 'ref', lambda *args: None)
        result = murano_object_weak_ref.__call__()

        self.assertEqual(mock.sentinel.res, result)
        self.assertEqual('weakref',
                         murano_object_weak_ref.ref.__class__.__name__)

    def test_weak_ref_with_null_obj(self):
        self.assertIsNone(helpers.weak_ref(None))

    @mock.patch.object(helpers, 're', autospec=True)
    def test_parse_type_string_with_null_res(self, mock_re):
        mock_re.compile.return_value = mock.Mock(
            **{'match.return_value': None})
        self.assertIsNone(helpers.parse_type_string('', None, None))

    def test_format_type_string(self):
        inner_type_obj = mock.Mock(spec=dsl_types.MuranoType)
        inner_type_obj.configure_mock(**{'name': 'foo', 'version': 'foo_ver'})
        inner_type_obj_pkg = mock.Mock()
        inner_type_obj_pkg.configure_mock(name='foo_pkg')
        setattr(inner_type_obj, 'package', inner_type_obj_pkg)
        type_obj = mock.Mock(spec=dsl_types.MuranoTypeReference,
                             type=inner_type_obj)
        result = helpers.format_type_string(type_obj)
        self.assertEqual('foo/foo_ver@foo_pkg', result)

    def test_format_type_string_except_value_error(self):
        type_obj = mock.Mock(spec=dsl_types.MuranoTypeReference, type=None)
        e = self.assertRaises(ValueError, helpers.format_type_string, type_obj)
        self.assertEqual('Invalid argument', str(e))

    def test_patch_dict(self):
        path = 'foo.bar.baz'
        fake_dict = mock.MagicMock(spec=dict)
        # Make the dict return itself to test whether all the parts are called.
        fake_dict.get.return_value = fake_dict
        helpers.patch_dict(fake_dict, path, None)
        fake_dict.get.assert_has_calls([mock.call('foo'), mock.call('bar')])
        fake_dict.pop.assert_not_called()

    def test_patch_dict_without_dict(self):
        path = 'foo.bar.baz'
        not_a_dict = mock.Mock()
        helpers.patch_dict(not_a_dict, path, None)
        not_a_dict.get.assert_not_called()
        not_a_dict.pop.assert_not_called()

    @mock.patch.object(helpers, 'gc')
    def test_walk_gc_with_towards_true(self, mock_gc, autospec=True):
        mock_gc.get_referrers.side_effect = [
            [mock.sentinel.second], [mock.sentinel.third]
        ]
        first_obj = mock.sentinel.first
        handler = mock.MagicMock()
        handler.return_value = True

        expected = [
            [mock.sentinel.first],
            [mock.sentinel.first, mock.sentinel.second],
            [mock.sentinel.first, mock.sentinel.second, mock.sentinel.third]
        ]
        actual = []
        for obj in helpers.walk_gc(first_obj, True, handler):
            actual.append(obj)
        self.assertEqual(expected, actual)

    @mock.patch.object(helpers, 'gc', autospec=True)
    def test_walk_gc_with_towards_false(self, mock_gc):
        mock_gc.get_referents.side_effect = [
            # Trigger the continue by duplicating entries.
            [mock.sentinel.second], [mock.sentinel.second]
        ]
        first_obj = mock.sentinel.first
        handler = mock.MagicMock()
        handler.return_value = True

        expected = [
            [mock.sentinel.first],
            [mock.sentinel.second, mock.sentinel.first]
        ]
        actual = []
        for obj in helpers.walk_gc(first_obj, False, handler):
            actual.append(obj)
        self.assertEqual(expected, actual)


class TestMergeDicts(base.MuranoTestCase):
    def check(self, dict1, dict2, expected):
        result = helpers.merge_dicts(dict1, dict2)
        self.assertEqual(expected, result)

    def test_dicts_plain(self):
        dict1 = {"a": "1"}
        dict2 = {"a": "100", "ab": "12"}
        expected = {"a": "100", "ab": "12"}
        self.check(dict1, dict2, expected)

    def test_different_types_none(self):
        dict1 = {"a": "1"}
        dict2 = {"a": None, "ab": "12"}
        expected = {"a": "1", "ab": "12"}
        self.check(dict1, dict2, expected)

    def test_different_types_of_iterable(self):
        dict1 = {"a": {"ab": "1"}}
        dict2 = {"a": ["ab", "1"]}
        self.assertRaises(TypeError, helpers.merge_dicts, dict1, dict2)

    def test_merge_nested_dicts(self):
        dict1 = {"a": {"ab": {}, "abc": "1"}}
        dict2 = {"a": {"abc": "123"}}
        expected = {"a": {"ab": {}, "abc": "123"}}
        self.check(dict1, dict2, expected)

    def test_merge_nested_dicts_with_max_levels(self):
        dict1 = {"a": {"ab": {"abcd": "1234"}, "abc": "1"}}
        dict2 = {"a": {"ab": {"y": "9"}, "abc": "123"}}
        expected = {"a": {"ab": {"y": "9"}, "abc": "123"}}
        result = helpers.merge_dicts(dict1, dict2, max_levels=2)
        self.assertEqual(expected, result)

    def test_merge_with_lists(self):
        dict1 = {"a": [1, 2]}
        dict2 = {"a": [1, 3, 2, 4]}
        expected = {"a": [1, 2, 3, 4]}
        self.check(dict1, dict2, expected)


class TestParseVersionSpec(base.MuranoTestCase):
    def check(self, expected, version_spec):
        self.assertEqual(expected, helpers.parse_version_spec(version_spec))

    def test_empty_version_spec(self):
        version_spec = ""
        expected = semantic_version.Spec('>=0.0.0', '<1.0.0-0')
        self.check(expected, version_spec)

    def test_empty_kind(self):
        version_spec = "1.11.111"
        expected = semantic_version.Spec('==1.11.111')
        self.check(expected, version_spec)

    def test_implicit_major(self):
        version_spec = ">=2"
        expected = semantic_version.Spec('>=2.0.0')
        self.check(expected, version_spec)

    def test_implicit_minor(self):
        version_spec = ">=2.1"
        expected = semantic_version.Spec('>=2.1.0')
        self.check(expected, version_spec)

    def test_remove_spaces(self):
        version_spec = "< =  2 .1"
        expected = semantic_version.Spec('<2.2.0-0')
        self.check(expected, version_spec)

    def test_input_version(self):
        version_spec = semantic_version.Version('1.11.111')
        expected = semantic_version.Spec('==1.11.111')
        self.check(expected, version_spec)

    def test_input_spec(self):
        version_spec = semantic_version.Spec('<=1', '<=1.11')
        expected = semantic_version.Spec('<1.12.0-0', '<2.0.0-0')
        self.check(expected, version_spec)
