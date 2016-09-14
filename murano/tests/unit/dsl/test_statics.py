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


from yaql.language import exceptions as yaql_exceptions
from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestStatics(test_case.DslTestCase):
    def setUp(self):
        @dsl.name('test.TestStatics')
        class PythonClass(object):
            @staticmethod
            @specs.parameter('arg', yaqltypes.Integer())
            @specs.inject('receiver', yaqltypes.Receiver())
            def static_python_method(arg, receiver):
                if isinstance(receiver, dsl_types.MuranoObjectInterface):
                    return 3 * arg
                return 7 * arg

            @classmethod
            @specs.inject('receiver', yaqltypes.Receiver())
            def classmethod_python_method(cls, arg, receiver):
                if isinstance(receiver, dsl_types.MuranoObjectInterface):
                    return cls.__name__.upper() + str(arg)
                return cls.__name__ + str(arg)

        super(TestStatics, self).setUp()
        self.package_loader.load_class_package(
            'test.TestStatics', None).register_class(PythonClass)
        self._runner = self.new_runner(
            om.Object('test.TestStatics', staticProperty2='INVALID'))

    def test_call_static_method_on_object(self):
        self.assertEqual(123, self._runner.testCallStaticMethodOnObject())

    def test_call_static_method_on_class_name(self):
        self.assertEqual(123, self._runner.testCallStaticMethodOnClassName())

    def test_call_static_method_on_class_name_with_ns(self):
        self.assertEqual(
            678, self._runner.testCallStaticMethodOnClassNameWithNs())

    def test_call_static_method_from_another_method(self):
        self.assertEqual(
            123 * 5, self._runner.testCallStaticMethodFromAnotherMethod())

    def test_static_this(self):
        self.assertIsInstance(
            self._runner.testStaticThis(), dsl_types.MuranoTypeReference)

    def test_no_access_to_instance_properties(self):
        self.assertRaises(
            exceptions.NoPropertyFound,
            self._runner.testNoAccessToInstanceProperties)

    def test_access_static_property_from_instance_method(self):
        self.assertEqual(
            'xxx', self._runner.testAccessStaticPropertyFromInstanceMethod())

    def test_access_static_property_from_static_method(self):
        self.assertEqual(
            'xxx', self._runner.testAccessStaticPropertyFromStaticMethod())

    def test_modify_static_property_using_dollar(self):
        self.assertEqual(
            'qq', self._runner.testModifyStaticPropertyUsingDollar())

    def test_modify_static_property_using_this(self):
        self.assertEqual(
            'qq', self._runner.testModifyStaticPropertyUsingThis())

    def test_modify_static_property_using_class_name(self):
        self.assertEqual(
            'qq', self._runner.testModifyStaticPropertyUsingClassName())

    def test_modify_static_property_using_ns_class_name(self):
        self.assertEqual(
            'qq', self._runner.testModifyStaticPropertyUsingNsClassName())

    def test_modify_static_property_using_type_func(self):
        self.assertEqual(
            'qq', self._runner.testModifyStaticPropertyUsingTypeFunc())

    def test_modify_static_dict_property(self):
        self.assertEqual(
            {'key': 'value'}, self._runner.testModifyStaticDictProperty())

    def test_property_is_static(self):
        self.assertEqual('qq', self._runner.testPropertyIsStatic())

    def test_static_properties_excluded_from_object_model(self):
        self.assertEqual(
            'staticProperty',
            self._runner.testStaticPropertisNotLoaded())

    def test_type_is_singleton(self):
        self.assertTrue(self._runner.testTypeIsSingleton())

    def test_static_property_inheritance(self):
        self.assertEqual(
            'baseStaticProperty' * 3,
            self._runner.testStaticPropertyInheritance())

    def test_static_property_override(self):
        self.assertEqual(
            [
                'conflictingStaticProperty-child',
                'conflictingStaticProperty-child',
                'conflictingStaticProperty-base',
                'conflictingStaticProperty-child',
                'conflictingStaticProperty-base'
            ], self._runner.testStaticPropertyOverride())

    def test_type_info_of_type(self):
        self.assertTrue(self._runner.testTypeinfoOfType())

    def test_call_python_static_method(self):
        self.assertEqual(
            [333] + [777] * 3,
            self._runner.testCallPythonStaticMethod())

    def test_call_python_classmethod(self):
        self.assertEqual(
            ['PYTHONCLASS!'] + ['PythonClass!'] * 3,
            self._runner.testCallPythonClassMethod())

    def test_call_static_method_on_invalid_class(self):
        self.assertRaises(
            yaql_exceptions.NoMatchingMethodException,
            self._runner.testCallStaticMethodOnInvalidClass)

    def test_static_method_callable_from_python(self):
        self.assertEqual(
            'It works!',
            self._runner.on_class('test.TestStatics').testStaticAction())
