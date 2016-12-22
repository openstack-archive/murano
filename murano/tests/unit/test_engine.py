# Copyright (c) 2014 Mirantis Inc.
#
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

import re

import mock
import semantic_version
import six
import yaql
from yaql.language import exceptions
from yaql.language import utils

import murano.dsl.helpers as helpers
import murano.dsl.namespace_resolver as ns_resolver
import murano.dsl.yaql_expression as yaql_expression
from murano.tests.unit import base

ROOT_CLASS = 'io.murano.Object'


class TestNamespaceResolving(base.MuranoTestCase):
    def test_fails_w_empty_name(self):
        resolver = ns_resolver.NamespaceResolver({'=': 'com.example.murano'})

        self.assertRaises(ValueError, resolver.resolve_name, None)

    def test_fails_w_unknown_prefix(self):
        resolver = ns_resolver.NamespaceResolver({'=': 'com.example.murano'})
        name = 'unknown_prefix:example.murano'

        self.assertRaises(KeyError, resolver.resolve_name, name)

    def test_fails_w_prefix_wo_name(self):
        resolver = ns_resolver.NamespaceResolver({'=': 'com.example.murano'})
        name = 'sys:'

        self.assertRaises(ValueError, resolver.resolve_name, name)

    def test_fails_w_excessive_prefix(self):
        ns = {'sys': 'com.example.murano.system'}
        resolver = ns_resolver.NamespaceResolver(ns)
        invalid_name = 'sys:excessive_ns:muranoResource'

        self.assertRaises(ValueError, resolver.resolve_name, invalid_name)

    def test_empty_prefix_is_default(self):
        resolver = ns_resolver.NamespaceResolver({'=': 'com.example.murano'})
        # name without prefix delimiter
        name = 'some.arbitrary.name'

        resolved_name = resolver.resolve_name(':' + name)

        self.assertEqual(
            'com.example.murano.some.arbitrary.name', resolved_name)

    def test_resolves_specified_ns_prefix(self):
        ns = {'sys': 'com.example.murano.system'}
        resolver = ns_resolver.NamespaceResolver(ns)
        short_name, full_name = 'sys:File', 'com.example.murano.system.File'

        resolved_name = resolver.resolve_name(short_name)

        self.assertEqual(full_name, resolved_name)

    def test_resolves_current_ns(self):
        resolver = ns_resolver.NamespaceResolver({'=': 'com.example.murano'})
        short_name, full_name = 'Resource', 'com.example.murano.Resource'

        resolved_name = resolver.resolve_name(short_name)

        self.assertEqual(full_name, resolved_name)

    def test_resolves_w_empty_namespaces(self):
        resolver = ns_resolver.NamespaceResolver({})

        resolved_name = resolver.resolve_name('Resource')

        self.assertEqual('Resource', resolved_name)


class TestHelperFunctions(base.MuranoTestCase):
    def test_generate_id(self):
        generated_id = helpers.generate_id()

        self.assertTrue(re.match(r'[a-z0-9]{32}', generated_id))

    def test_evaluate(self):
        yaql_value = mock.Mock(yaql_expression.YaqlExpression,
                               return_value='atom')
        complex_value = {yaql_value: ['some', (1, yaql_value), 'hi!'],
                         'sample': [yaql_value, six.moves.range(5)]}
        complex_literal = utils.FrozenDict({
            'atom': ('some', (1, 'atom'), 'hi!'),
            'sample': ('atom', (0, 1, 2, 3, 4))
        })
        context = yaql.create_context()
        evaluated_value = helpers.evaluate(yaql_value, context)
        evaluated_complex_value = helpers.evaluate(complex_value, context)

        self.assertEqual('atom', evaluated_value)
        self.assertEqual(complex_literal, evaluated_complex_value)


class TestYaqlExpression(base.MuranoTestCase):
    def setUp(self):
        self._version = semantic_version.Version.coerce('1.0')
        super(TestYaqlExpression, self).setUp()

    def test_expression(self):
        yaql_expr = yaql_expression.YaqlExpression('string', self._version)

        self.assertEqual('string', yaql_expr.expression)

    def test_evaluate_calls(self):
        string = 'string'
        expected_calls = [mock.call(string, self._version),
                          mock.call().evaluate(context=None)]

        with mock.patch('murano.dsl.yaql_integration.parse') as mock_parse:
            yaql_expr = yaql_expression.YaqlExpression(string, self._version)
            yaql_expr(None)

        self.assertEqual(expected_calls, mock_parse.mock_calls)

    def test_is_expression_returns(self):
        expr = yaql_expression.YaqlExpression('string', self._version)

        with mock.patch('murano.dsl.yaql_integration.parse'):
            self.assertTrue(expr.is_expression('$some', self._version))
            self.assertTrue(expr.is_expression('$.someMore', self._version))

        with mock.patch('murano.dsl.yaql_integration.parse') as parse_mock:
            parse_mock.side_effect = exceptions.YaqlGrammarException
            self.assertFalse(expr.is_expression('', self._version))

        with mock.patch('murano.dsl.yaql_integration.parse') as parse_mock:
            parse_mock.side_effect = exceptions.YaqlLexicalException
            self.assertFalse(expr.is_expression('', self._version))

    def test_property(self):
        self.assertRaises(TypeError,
                          yaql_expression.YaqlExpression,
                          None, self._version)

        expr = yaql_expression.YaqlExpression('string', self._version)
        self.assertEqual(expr._version, expr.version)
        self.assertIsNone(expr._file_position)

        yaql_rep = expr.__repr__()
        self.assertEqual('YAQL(%s)' % expr._expression, yaql_rep)
