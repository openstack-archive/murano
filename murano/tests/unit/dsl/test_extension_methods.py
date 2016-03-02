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


from yaql.language import exceptions
from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import dsl
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestExtensionMethods(test_case.DslTestCase):
    def setUp(self):
        @dsl.name('extcls.Extender')
        class PythonClass(object):
            def __init__(self, arg):
                self.value = arg

            @staticmethod
            @specs.meta('Usage', 'Extension')
            @specs.parameter('arg', yaqltypes.Integer())
            def python_extension(arg):
                return arg * arg

            @classmethod
            @specs.meta('Usage', 'Extension')
            @specs.parameter('arg', yaqltypes.Integer())
            def python_extension2(cls, arg):
                return cls(2 * arg).value

        super(TestExtensionMethods, self).setUp()
        self.package_loader.load_class_package(
            'extcls.Extender', None).register_class(PythonClass)

        self._runner = self.new_runner(om.Object('extcls.TestClass'))

    def test_call_self_extension_method(self):
        self.assertEqual([123, 123], self._runner.testSelfExtensionMethod())

    def test_call_imported_extension_method(self):
        self.assertEqual(
            [246, 246], self._runner.testImportedExtensionMethod())

    def test_call_nullable_extension_method(self):
        self.assertEqual(
            [123, None], self._runner.testNullableExtensionMethod())

    def test_extensions_precedence(self):
        self.assertEqual(111, self._runner.testExtensionsPrecedence())

    def test_explicit_call(self):
        self.assertEqual(222, self._runner.testCallExtensionExplicitly())

    def test_explicit_call_on_instance_fails(self):
        self.assertRaises(
            exceptions.NoMatchingMethodException,
            self._runner.testExplicitCallDoenstWorkOnInstance)

    def test_call_on_primitive_types(self):
        self.assertEqual('qWERTy', self._runner.testCallOnPrimitiveTypes())

    def test_call_python_extension(self):
        self.assertEqual(16, self._runner.testCallPythonExtension())

    def test_call_python_extension_explicitly(self):
        self.assertEqual(25, self._runner.testCallPythonExtensionExplicitly())

    def test_call_python_classmethod_extension(self):
        self.assertEqual(14, self._runner.testCallPythonClassmethodExtension())
