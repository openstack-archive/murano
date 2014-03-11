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
import unittest

import mock
import yaql

from muranoapi.engine import classes
from muranoapi.engine import consts
from muranoapi.engine import exceptions
from muranoapi.engine import helpers
from muranoapi.engine import namespaces
from muranoapi.engine import objects
from muranoapi.engine import typespec
from muranoapi.engine import yaql_expression


class TestNamespaceResolving(unittest.TestCase):
    def test_fails_w_empty_name(self):
        resolver = namespaces.NamespaceResolver({'=': 'com.example.murano'})

        self.assertRaises(ValueError, resolver.resolve_name, None)

    def test_fails_w_unknown_prefix(self):
        resolver = namespaces.NamespaceResolver({'=': 'com.example.murano'})
        name = 'unknown_prefix:example.murano'

        self.assertRaises(KeyError, resolver.resolve_name, name)

    def test_fails_w_prefix_wo_name(self):
        resolver = namespaces.NamespaceResolver({'=': 'com.example.murano'})
        name = 'sys:'

        self.assertRaises(NameError, resolver.resolve_name, name)

    def test_fails_w_excessive_prefix(self):
        ns = {'sys': 'com.example.murano.system'}
        resolver = namespaces.NamespaceResolver(ns)
        invalid_name = 'sys:excessive_ns:muranoResource'

        self.assertRaises(NameError, resolver.resolve_name, invalid_name)

    def test_cuts_empty_prefix(self):
        resolver = namespaces.NamespaceResolver({'=': 'com.example.murano'})
        # name without prefix delimiter
        name = 'some.arbitrary.name'

        resolved_name = resolver.resolve_name(':' + name)

        self.assertEqual(name, resolved_name)

    def test_resolves_specified_ns_prefix(self):
        ns = {'sys': 'com.example.murano.system'}
        resolver = namespaces.NamespaceResolver(ns)
        short_name, full_name = 'sys:File', 'com.example.murano.system.File'

        resolved_name = resolver.resolve_name(short_name)

        self.assertEqual(full_name, resolved_name)

    def test_resolves_current_ns(self):
        resolver = namespaces.NamespaceResolver({'=': 'com.example.murano'})
        short_name, full_name = 'Resource', 'com.example.murano.Resource'

        resolved_name = resolver.resolve_name(short_name)

        self.assertEqual(full_name, resolved_name)

    def test_resolves_explicit_base(self):
        resolver = namespaces.NamespaceResolver({'=': 'com.example.murano'})

        resolved_name = resolver.resolve_name('Resource', relative='com.base')

        self.assertEqual('com.base.Resource', resolved_name)

    def test_resolves_explicit_base_w_empty_namespaces(self):
        resolver = namespaces.NamespaceResolver({})

        resolved_name = resolver.resolve_name('File', 'com.base')

        self.assertEqual('com.base.File', resolved_name)

    def test_resolves_w_empty_namespaces(self):
        resolver = namespaces.NamespaceResolver({})

        resolved_name = resolver.resolve_name('Resource')

        self.assertEqual('Resource', resolved_name)


class Bunch(object):
    def __init__(self, **kwargs):
        super(Bunch, self).__init__()
        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class TestClassesManipulation(unittest.TestCase):
    resolver = mock.Mock(resolve_name=lambda name: name)

    def test_class_name(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)

        self.assertEqual(consts.ROOT_CLASS, cls.name)

    def test_class_namespace_resolver(self):
        resolver = namespaces.NamespaceResolver({})
        cls = classes.MuranoClass(None, resolver, consts.ROOT_CLASS)

        self.assertEqual(resolver, cls.namespace_resolver)

    def test_root_class_has_no_parents(self):
        root_class = classes.MuranoClass(
            None, self.resolver, consts.ROOT_CLASS, ['You should not see me!'])

        self.assertEqual([], root_class.parents)

    def test_non_root_class_resolves_parents(self):
        root_cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        class_loader = mock.Mock(get_class=lambda name: root_cls)
        desc_cls1 = classes.MuranoClass(class_loader, self.resolver, 'Obj')
        desc_cls2 = classes.MuranoClass(
            class_loader, self.resolver, 'Obj', [root_cls])

        self.assertEqual([root_cls], desc_cls1.parents)
        self.assertEqual([root_cls], desc_cls2.parents)

    def test_class_initial_properties(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        self.assertEqual([], cls.properties)

    def test_fails_add_incompatible_property_to_class(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        kwargs = {'name': 'sampleProperty', 'property_typespec': {}}

        self.assertRaises(TypeError, cls.add_property, **kwargs)

    def test_add_property_to_class(self):
        prop = typespec.PropertySpec({'Default': 1}, self.resolver)
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls.add_property('firstPrime', prop)

        class_properties = cls.properties
        class_property = cls.get_property('firstPrime')

        self.assertEqual(['firstPrime'], class_properties)
        self.assertEqual(prop, class_property)

    def test_class_property_search(self):
        void_prop = typespec.PropertySpec({'Default': 'Void'}, self.resolver)
        mother_prop = typespec.PropertySpec({'Default': 'Mother'},
                                            self.resolver)
        father_prop = typespec.PropertySpec({'Default': 'Father'},
                                            self.resolver)
        child_prop = typespec.PropertySpec({'Default': 'Child'},
                                           self.resolver)
        root = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        mother = classes.MuranoClass(None, self.resolver, 'Mother', [root])
        father = classes.MuranoClass(None, self.resolver, 'Father', [root])
        child = classes.MuranoClass(
            None, self.resolver, 'Child', [mother, father])

        root.add_property('Void', void_prop)
        mother.add_property('Mother', mother_prop)
        father.add_property('Father', father_prop)
        child.add_property('Child', child_prop)

        self.assertEqual(child_prop, child.find_property('Child'))
        self.assertEqual(father_prop, child.find_property('Father'))
        self.assertEqual(mother_prop, child.find_property('Mother'))
        self.assertEqual(void_prop, child.find_property('Void'))

    def test_class_is_compatible(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        descendant_cls = classes.MuranoClass(
            None, self.resolver, 'DescendantCls', [cls])
        obj = mock.Mock(spec=objects.MuranoObject)
        descendant_obj = mock.Mock(spec=objects.MuranoObject)
        obj.type = cls
        descendant_obj.type = descendant_cls
        descendant_obj.parents = [obj]

        self.assertTrue(cls.is_compatible(obj))
        self.assertTrue(cls.is_compatible(descendant_obj))
        self.assertFalse(descendant_cls.is_compatible(obj))

    def test_new_method_calls_initialize(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls.object_class = mock.Mock()

        with mock.patch('inspect.getargspec') as spec_mock:
            spec_mock.return_value = Bunch(args=())
            obj = cls.new(None, None, None, {})

            self.assertTrue(obj.initialize.called)

    def test_new_method_not_calls_initialize(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls.object_class = mock.Mock()

        obj = cls.new(None, None, None)

        self.assertFalse(obj.initialize.called)


class TestObjectsManipulation(unittest.TestCase):
    def setUp(self):
        self.resolver = mock.Mock(resolve_name=lambda name: name)
        self.cls = mock.Mock()
        self.cls.name = consts.ROOT_CLASS
        self.cls.parents = []

    def test_object_valid_type_instantiation(self):
        obj = objects.MuranoObject(self.cls, None, None, None)

        self.assertEqual(self.cls, obj.type)

    def test_object_own_properties_initialization(self):
        # TODO: there should be test for initializing first non-dependent
        # object properties, then the dependent ones (given as
        # YAQL-expressions)
        pass

    def test_object_parent_properties_initialization(self):
        root = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls = classes.MuranoClass(None, self.resolver, 'SomeClass', [root])
        root.new = mock.Mock()
        init_kwargs = {'theArg': 0}
        obj = objects.MuranoObject(cls, None, None, None)
        expected_calls = [mock.call().initialize(**init_kwargs)]

        obj.initialize(**init_kwargs)

        # each object should also initialize his parent objects
        self.assertEqual(expected_calls, root.new.mock_calls[1:])

    def test_object_id(self):
        _id = 'some_id'
        patch_at = 'muranoapi.engine.objects.helpers.generate_id'

        obj = objects.MuranoObject(self.cls, None, None, None, object_id=_id)
        with mock.patch(patch_at) as gen_id_mock:
            gen_id_mock.return_value = _id
            obj1 = objects.MuranoObject(self.cls, None, None, None)

        self.assertEqual(_id, obj.object_id)
        self.assertEqual(_id, obj1.object_id)

    def test_parent_obj(self):
        parent = mock.Mock()
        obj = objects.MuranoObject(self.cls, parent, None, None)

        self.assertEqual(parent, obj.parent)

    def test_fails_internal_property_access(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)

        cls.add_property('__hidden',
                         typespec.PropertySpec({'Default': 10}, self.resolver))
        obj = objects.MuranoObject(cls, None, None, None)

        self.assertRaises(AttributeError, lambda: obj.__hidden)

    def test_proper_property_access(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)

        cls.add_property('someProperty',
                         typespec.PropertySpec({'Default': 0}, self.resolver))
        obj = cls.new(None, None, None, {})

        self.assertEqual(0, obj.someProperty)

    def test_parent_class_property_access(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        child_cls = classes.MuranoClass(None, self.resolver, 'Child', [cls])

        cls.add_property('anotherProperty',
                         typespec.PropertySpec({'Default': 0}, self.resolver))
        obj = child_cls.new(None, None, None, {})

        self.assertEqual(0, obj.anotherProperty)

    def test_fails_on_parents_property_collision(self):
        root = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        mother = classes.MuranoClass(None, self.resolver, 'Mother', [root])
        father = classes.MuranoClass(None, self.resolver, 'Father', [root])
        child = classes.MuranoClass(
            None, self.resolver, 'Child', [mother, father])

        mother.add_property(
            'conflictProp',
            typespec.PropertySpec({'Default': 0}, self.resolver))
        father.add_property(
            'conflictProp',
            typespec.PropertySpec({'Default': 0}, self.resolver))
        obj = child.new(None, None, None, {})

        self.assertRaises(LookupError, lambda: obj.conflictProp)

    def test_fails_setting_undeclared_property(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        obj = cls.new(None, None, None, {})

        self.assertRaises(AttributeError, obj.set_property, 'newOne', 10)

    def test_set_undeclared_property_as_internal(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        obj = cls.new(None, None, None, {})
        obj.cast = mock.Mock(return_value=obj)
        prop_value = 10

        obj.set_property('internalProp', prop_value, caller_class=cls)
        resolved_value = obj.get_property('internalProp', caller_class=cls)

        self.assertEqual(prop_value, resolved_value)

    def test_fails_forbidden_set_property(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls.add_property('someProperty',
                         typespec.PropertySpec({'Default': 0}, self.resolver))
        cls.is_compatible = mock.Mock(return_value=False)
        obj = cls.new(None, None, None, {})

        self.assertRaises(exceptions.NoWriteAccess, obj.set_property,
                          'someProperty', 10, caller_class=cls)

    def test_set_property(self):
        cls = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls.add_property('someProperty',
                         typespec.PropertySpec({'Default': 0}, self.resolver))
        obj = cls.new(None, None, None, {})

        with mock.patch('yaql.context.Context'):
            with mock.patch('muranoapi.engine.helpers') as helpers_mock:
                helpers_mock.evaluate = lambda val, ctx, _: val
                obj.set_property('someProperty', 10)

        self.assertEqual(10, obj.someProperty)

    def test_set_parent_property(self):
        root = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls = classes.MuranoClass(None, self.resolver, 'SomeClass', [root])
        root.add_property('rootProperty',
                          typespec.PropertySpec({'Default': 0}, self.resolver))
        obj = cls.new(None, None, None, {})

        with mock.patch('muranoapi.engine.helpers') as helpers_mock:
            with mock.patch('yaql.context.Context'):
                helpers_mock.evaluate = lambda val, ctx, _: val
                obj.set_property('rootProperty', 20)

        self.assertEqual(20, obj.rootProperty)

    def test_object_up_cast(self):
        root = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        root_alt = classes.MuranoClass(None, self.resolver, 'RootAlt', [])
        cls = classes.MuranoClass(
            None, self.resolver, 'SomeClass', [root, root_alt])
        root_obj = root.new(None, None, None)
        cls_obj = cls.new(None, None, None)

        root_obj_casted2root = root_obj.cast(root)
        cls_obj_casted2root = cls_obj.cast(root)
        cls_obj_casted2root_alt = cls_obj.cast(root_alt)

        self.assertEqual(root_obj, root_obj_casted2root)
        # each object creates an _internal_ parent objects hierarchy,
        # so direct comparison of objects is not possible
        self.assertEqual(root, cls_obj_casted2root.type)
        self.assertEqual(root_alt, cls_obj_casted2root_alt.type)

    def test_fails_object_down_cast(self):
        root = classes.MuranoClass(None, self.resolver, consts.ROOT_CLASS)
        cls = classes.MuranoClass(
            None, self.resolver, 'SomeClass', [root])
        root_obj = root.new(None, None, None)

        self.assertRaises(TypeError, root_obj.cast, cls)


class TestHelperFunctions(unittest.TestCase):
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

        evaluated_value = helpers.evaluate(yaql_value, None, 1)
        non_evaluated_value = helpers.evaluate(yaql_value, None, 0)
        evaluated_complex_value = helpers.evaluate(complex_value, None)
        non_evaluated_complex_value = helpers.evaluate(
            complex_value, None, complex_literal_depth)

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


class TestYaqlExpression(unittest.TestCase):
    def test_expression(self):
        yaql_expr = yaql_expression.YaqlExpression('string')

        self.assertEqual('string', yaql_expr.expression())

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
