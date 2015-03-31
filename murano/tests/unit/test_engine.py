# coding: utf-8
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
import yaql

import murano.dsl.helpers as helpers
import murano.dsl.namespace_resolver as ns_resolver
import murano.dsl.yaql_expression as yaql_expression
from murano.tests.unit import base

ROOT_CLASS = 'io.murano.Object'


class TestNamespaceResolving(base.MuranoTestCase):

    def setUp(self):
        super(TestNamespaceResolving, self).setUp()

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

        self.assertRaises(NameError, resolver.resolve_name, name)

    def test_fails_w_excessive_prefix(self):
        ns = {'sys': 'com.example.murano.system'}
        resolver = ns_resolver.NamespaceResolver(ns)
        invalid_name = 'sys:excessive_ns:muranoResource'

        self.assertRaises(NameError, resolver.resolve_name, invalid_name)

    def test_cuts_empty_prefix(self):
        resolver = ns_resolver.NamespaceResolver({'=': 'com.example.murano'})
        # name without prefix delimiter
        name = 'some.arbitrary.name'

        resolved_name = resolver.resolve_name(':' + name)

        self.assertEqual(name, resolved_name)

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

    def test_resolves_explicit_base(self):
        resolver = ns_resolver.NamespaceResolver({'=': 'com.example.murano'})

        resolved_name = resolver.resolve_name('Resource', relative='com.base')

        self.assertEqual('com.base.Resource', resolved_name)

    def test_resolves_explicit_base_w_empty_namespaces(self):
        resolver = ns_resolver.NamespaceResolver({})

        resolved_name = resolver.resolve_name('File', 'com.base')

        self.assertEqual('com.base.File', resolved_name)

    def test_resolves_w_empty_namespaces(self):
        resolver = ns_resolver.NamespaceResolver({})

        resolved_name = resolver.resolve_name('Resource')

        self.assertEqual('Resource', resolved_name)


class Bunch(object):
    def __init__(self, **kwargs):
        super(Bunch, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class TestHelperFunctions(base.MuranoTestCase):

    def setUp(self):
        super(TestHelperFunctions, self).setUp()

    def test_generate_id(self):
        generated_id = helpers.generate_id()

        self.assertTrue(re.match(r'[a-z0-9]{32}', generated_id))

    def test_evaluate(self):
        yaql_value = mock.Mock(spec=yaql_expression.YaqlExpression,
                               evaluate=lambda context: 'atom')
        complex_value = {yaql_value: ['some', (1, yaql_value), lambda: 'hi!'],
                         'sample': [yaql_value, xrange(5)]}
        complex_literal = {'atom': ['some', (1, 'atom'), 'hi!'],
                           'sample': ['atom', [0, 1, 2, 3, 4]]}
        # tuple(evaluate(list)) transformation adds + 1
        complex_literal_depth = 3 + 1

        context = yaql.create_context(False)
        evaluated_value = helpers.evaluate(yaql_value, context, 1)
        non_evaluated_value = helpers.evaluate(yaql_value, context, 0)
        evaluated_complex_value = helpers.evaluate(complex_value, context)
        non_evaluated_complex_value = helpers.evaluate(
            complex_value, context, complex_literal_depth)

        self.assertEqual('atom', evaluated_value)
        self.assertNotEqual('atom', non_evaluated_value)
        self.assertEqual(complex_literal, evaluated_complex_value)
        self.assertNotEqual(complex_literal, non_evaluated_complex_value)

    def test_needs_evaluation(self):
        testee = helpers.needs_evaluation
        parsed_expr = yaql.parse("string")
        yaql_expr = yaql_expression.YaqlExpression("string")

        self.assertTrue(testee(parsed_expr))
        self.assertTrue(testee(yaql_expr))
        self.assertTrue(testee({yaql_expr: 1}))
        self.assertTrue(testee({'label': yaql_expr}))
        self.assertTrue(testee([yaql_expr]))


class TestYaqlExpression(base.MuranoTestCase):

    def setUp(self):
        super(TestYaqlExpression, self).setUp()

    def test_expression(self):
        yaql_expr = yaql_expression.YaqlExpression('string')

        self.assertEqual('string', yaql_expr.expression)

    def test_unicode_expression(self):
        yaql_expr = yaql_expression.YaqlExpression(u"'yaql ♥ unicode'")

        self.assertEqual(u"'yaql ♥ unicode'".encode('utf-8'),
                         yaql_expr.expression)

    def test_unicode_expression_expression(self):
        yaql_expr = yaql_expression.YaqlExpression(u"'yaql ♥ unicode'")
        yaql_expr2 = yaql_expression.YaqlExpression(yaql_expr)

        self.assertEqual(u"'yaql ♥ unicode'".encode('utf-8'),
                         yaql_expr2.expression)

    def test_evaluate_calls(self):
        string = 'string'
        expected_calls = [mock.call(string),
                          mock.call().evaluate(context=None)]

        with mock.patch('yaql.parse') as mock_parse:
            yaql_expr = yaql_expression.YaqlExpression(string)
            yaql_expr.evaluate()

        self.assertEqual(expected_calls, mock_parse.mock_calls)

    def test_match_returns(self):
        expr = yaql_expression.YaqlExpression('string')

        with mock.patch('yaql.parse'):
            self.assertTrue(expr.match('$some'))
            self.assertTrue(expr.match('$.someMore'))

        with mock.patch('yaql.parse') as parse_mock:
            parse_mock.side_effect = yaql.exceptions.YaqlGrammarException
            self.assertFalse(expr.match(''))

        with mock.patch('yaql.parse') as parse_mock:
            parse_mock.side_effect = yaql.exceptions.YaqlLexicalException
            self.assertFalse(expr.match(''))
