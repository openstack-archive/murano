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

from testtools import matchers

from murano.dsl import schema_generator
from murano.tests.unit.dsl.foundation import runner
from murano.tests.unit.dsl.foundation import test_case


class TestSchemaGeneration(test_case.DslTestCase):
    def setUp(self):
        super(TestSchemaGeneration, self).setUp()
        schema = schema_generator.generate_schema(
            self.package_loader, runner.TestContextManager({}),
            'TestSchema')

        self._class_schema = schema.pop('')
        self._model_builders_schema = schema

    def test_general_structure(self):
        self.assertIn('$schema', self._class_schema)
        self.assertIn('type', self._class_schema)
        self.assertIn('properties', self._class_schema)
        self.assertEqual(
            'http://json-schema.org/draft-04/schema#',
            self._class_schema['$schema'])
        self.assertEqual('object', self._class_schema['type'])

    def _test_simple_property(self, name_or_schema, types):
        if not isinstance(name_or_schema, dict):
            props = self._class_schema['properties']
            self.assertIn(name_or_schema, props)
            schema = props[name_or_schema]
        else:
            schema = name_or_schema
        self.assertIn('type', schema)
        if isinstance(types, list):
            self.assertItemsEqual(schema['type'], types)
        else:
            self.assertEqual(schema['type'], types)
        return schema

    def test_string_property(self):
        self._test_simple_property('stringProperty', ['null', 'string'])

    def test_not_null_string_property(self):
        self._test_simple_property('stringNotNullProperty', 'string')

    def test_int_property(self):
        self._test_simple_property('intProperty', ['null', 'integer'])

    def test_not_null_int_property(self):
        self._test_simple_property('intNotNullProperty', 'integer')

    def test_bool_property(self):
        self._test_simple_property('boolProperty', ['null', 'boolean'])

    def test_not_null_bool_property(self):
        self._test_simple_property('boolNotNullProperty', 'boolean')

    def test_class_property(self):
        schema = self._test_simple_property(
            'classProperty', ['null', 'muranoObject'])
        self.assertEqual('SampleClass1', schema.get('muranoType'))

    def test_template_property(self):
        schema = self._test_simple_property(
            'templateProperty', ['null', 'muranoObject'])
        self.assertEqual('SampleClass1', schema.get('muranoType'))
        self.assertTrue(schema.get('owned'))
        self.assertItemsEqual(
            ['stringProperty'],
            schema.get('excludedProperties'))

    def test_default_property(self):
        schema = self._test_simple_property(
            'defaultProperty', ['null', 'integer'])
        self.assertEqual(999, schema.get('default'))

    def test_list_property(self):
        schema = self._test_simple_property('listProperty', 'array')
        self.assertIn('items', schema)
        items = schema['items']
        self._test_simple_property(items, 'string')

    def test_dict_property(self):
        schema = self._test_simple_property('dictProperty', 'object')
        self.assertIn('properties', schema)
        props = schema['properties']
        self.assertIn('key1', props)
        self._test_simple_property(props['key1'], 'string')
        self.assertIn('key2', props)
        self._test_simple_property(props['key2'], 'string')
        self.assertIn('additionalProperties', schema)
        extra_props = schema['additionalProperties']
        self._test_simple_property(extra_props, ['null', 'integer'])

    def test_complex_property(self):
        schema = self._test_simple_property('complexProperty', 'object')
        self.assertIn('properties', schema)
        self.assertEqual({}, schema['properties'])
        self.assertIn('additionalProperties', schema)
        extra_props = schema['additionalProperties']
        self._test_simple_property(extra_props, 'array')
        self.assertIn('items', extra_props)
        items = extra_props['items']
        self._test_simple_property(items, 'integer')

    def test_minimum_contract(self):
        schema = self._test_simple_property('minimumContract', 'integer')
        self.assertFalse(schema.get('exclusiveMinimum', True))
        self.assertEqual(5, schema.get('minimum'))

    def test_maximum_contract(self):
        schema = self._test_simple_property('maximumContract', 'integer')
        self.assertTrue(schema.get('exclusiveMaximum', False))
        self.assertEqual(15, schema.get('maximum'))

    def test_range_contract(self):
        schema = self._test_simple_property('rangeContract', 'integer')
        self.assertFalse(schema.get('exclusiveMaximum', True))
        self.assertTrue(schema.get('exclusiveMinimum', False))
        self.assertEqual(0, schema.get('minimum'))
        self.assertEqual(10, schema.get('maximum'))

    def test_chain_contract(self):
        schema = self._test_simple_property('chainContract', 'integer')
        self.assertFalse(schema.get('exclusiveMaximum', True))
        self.assertTrue(schema.get('exclusiveMinimum', False))
        self.assertEqual(0, schema.get('minimum'))
        self.assertEqual(10, schema.get('maximum'))

    def test_regex_contract(self):
        schema = self._test_simple_property('regexContract', 'string')
        self.assertEqual(r'\d+', schema.get('pattern'))

    def test_enum_contract(self):
        schema = self._test_simple_property('enumContract', 'string')
        self.assertEqual(['a', 'b'], schema.get('enum'))

    def test_enum_func_contract(self):
        schema = self._test_simple_property('enumFuncContract', 'string')
        self.assertEqual(['x', 'y'], schema.get('enum'))

    def test_ui_hints(self):
        schema = self._test_simple_property('decoratedProperty', 'string')
        self.assertEqual('Title!', schema.get('title'))
        self.assertEqual('Description!', schema.get('description'))
        self.assertEqual('Help!', schema.get('helpText'))
        self.assertFalse(schema.get('visible'))
        self.assertThat(schema.get('formIndex'), matchers.GreaterThan(-1))
        self.assertEqual('mySection', schema.get('formSection'))

        sections = self._class_schema.get('formSections')
        self.assertIsInstance(sections, dict)
        section = sections.get('mySection')
        self.assertIsInstance(section, dict)
        self.assertThat(section.get('index'), matchers.GreaterThan(-1))
        self.assertEqual('Section Title', section.get('title'))

    def test_model_builders(self):
        self.assertEqual(1, len(self._model_builders_schema))
        schema = self._model_builders_schema.get('modelBuilder')
        self.assertIsInstance(schema, dict)
        self._class_schema = schema
        self.test_general_structure()
        self.assertEqual('Model Builder!', schema.get('title'))
        args = schema['properties']
        self._test_simple_property(args.get('arg1'), 'string')
        self._test_simple_property(args.get('arg2'), 'integer')
        arg1 = args['arg1']
        self.assertEqual('Arg1!', arg1.get('title'))

    def test_generate_schema_with_extra_params(self):
        schema = schema_generator.generate_schema(
            self.package_loader, runner.TestContextManager({}),
            'TestSchema', method_names='modelBuilder',
            package_name='tests')
        expected_schema = {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'additionalProperties': False,
            'formSections': {},
            'properties': {'arg1': {'title': 'Arg1!',
                                    'type': 'string'},
                           'arg2': {'type': 'integer'}},
            'title': 'Model Builder!',
            'type': 'object'
        }

        self.assertIn('modelBuilder', schema)
        self.assertEqual(expected_schema, schema['modelBuilder'])

    def test_translate_list(self):
        contract = [1, 2, 3]
        result = schema_generator.translate_list(contract, None, None)
        self.assertEqual({'type': 'array'}, result)

        contract = [1, 2, 3, {'foo': 'bar'}]
        result = schema_generator.translate_list(contract, None, None)
        expected = {
            'items': {'additionalProperties': False,
                      'properties': {'foo': None},
                      'type': 'object'},
            'type': 'array'
        }
        self.assertEqual(sorted(expected.keys()), sorted(result.keys()))
        for key, val in expected.items():
            self.assertEqual(val, result[key])

        contract = [1, 2, 3, {'foo': 'bar'}, ['baz']]
        result = schema_generator.translate_list(contract, None, None)
        expected = {
            'additionalItems': {'items': None, 'type': 'array'},
            'items': [{'additionalProperties': False,
                       'properties': {'foo': None},
                       'type': 'object'},
                      {'items': None, 'type': 'array'}],
            'type': 'array'
        }
        self.assertEqual(sorted(expected.keys()), sorted(result.keys()))
        for key, val in expected.items():
            if isinstance(val, dict):
                for key_, val_ in val.items():
                    self.assertEqual(val_, val[key_])
            else:
                self.assertEqual(val, result[key])
