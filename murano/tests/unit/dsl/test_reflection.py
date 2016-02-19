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

from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestReflection(test_case.DslTestCase):
    def setUp(self):
        super(TestReflection, self).setUp()
        self._runner = self.new_runner(om.Object('TestReflection'))

    def test_type_info(self):
        self.assertEqual(
            {
                'name': 'TestReflection',
                'versionStr': '0.0.0',
                'versionMajor': 0,
                'versionMinor': 0,
                'versionPatch': 0,
                'ancestors': ['io.murano.Object'],
                'properties': ['property', 'staticProperty'],
                'package': 'tests',
                'methods': ['foo', 'getAttr', 'setAttr']
            },
            self._runner.testTypeInfo())

    def test_method_info(self):
        self.assertEqual(
            {
                'name': 'foo',
                'arguments': ['bar', 'baz'],
                'barHasDefault': True,
                'bazHasDefault': False,
                'barMethod': 'foo',
                'bazMethod': 'foo',
                'declaringType': 'TestReflection'
            },
            self._runner.testMethodInfo())

    def test_property_info(self):
        self.assertEqual(
            {
                'name': 'property',
                'hasDefault': True,
                'usage': 'InOut'
            },
            self._runner.testPropertyInfo())

    def test_property_read(self):
        self.assertEqual(
            [['object', 'static'], ['static']],
            self._runner.testPropertyRead())

    def test_property_write(self):
        self.assertEqual(
            [['new object', 'new static'], ['new static']],
            self._runner.testPropertyWrite())

    def test_method_invoke(self):
        self.assertEqual('bar baz', self._runner.testMethodInvoke())

    def test_instance_create(self):
        self.assertEqual('test', self._runner.testInstanceCreate())
