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

import six

from murano.dsl import dsl_types
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestDump(test_case.DslTestCase):
    def setUp(self):
        super(TestDump, self).setUp()
        self._runner = self.new_runner(om.Object('dumptests.TestDump'))

    def test_dump_simple_inline(self):
        source = om.Object('dumptests.DumpTarget1',
                           foo='FOO', bar=[40, 41, 42], baz={'BAZ': 99})
        result = self._runner.testDump(source, 'Inline')
        self.assertIn('id', result)
        res = self._get_body(result)
        self.assertEqual('FOO', res['foo'])
        self.assertEqual([40, 41, 42], res['bar'])
        self.assertEqual({'BAZ': 99}, res['baz'])

    def test_dump_simple_serializable(self):
        source = om.Object('dumptests.DumpTarget1',
                           foo='FOO', bar=[40, 41, 42], baz={'BAZ': 99})
        result = self._runner.testDump(source, 'Serializable')
        self.assertIn('?', result)
        self.assertEqual('dumptests.DumpTarget1/0.0.0@tests',
                         result['?']['type'])

    def test_dump_simple_full_mixed(self):
        source = om.Object('dumptests.DumpTarget1',
                           foo='FOO', bar=[40, 41, 42], baz={'BAZ': 99})

        result = self._runner.testDump(source, 'Mixed')
        self.assertIn('?', result)
        self.assertNotIn('classVersion', result['?'])
        self.assertNotIn('package', result['?'])
        self.assertIsInstance(result['?']['type'], dsl_types.MuranoType)
        self.assertEqual('dumptests.DumpTarget1', result['?']['type'].name)

    def test_nested(self):
        n1 = om.Object('dumptests.DumpTarget1', foo='FOO')
        n2 = om.Object('dumptests.DumpTarget1', foo='BAR')
        n3 = om.Object('dumptests.DumpTarget1', foo='BAZ')
        source = om.Object('dumptests.DumpTarget2',
                           nested=n1, another=n2, ref=n3)
        result = self._runner.testDump(source)
        res = self._get_body(result)
        self.assertIsNotNone(res['ref'])
        self.assertIsNotNone(res['another'])
        self.assertIsNotNone(res['nested'])
        self.assertEqual('FOO', self._get_body(res['nested'])['foo'])
        self.assertEqual('BAR', self._get_body(res['another'])['foo'])
        self.assertEqual('BAZ', self._get_body(res['ref'])['foo'])

    def test_same_ref_dump(self):
        nested = om.Object('dumptests.DumpTarget1', foo='FOO')
        source = om.Object('dumptests.DumpTarget2',
                           nested=nested, another=nested, ref=nested)
        result = self._runner.testDump(source)
        res = self._get_body(result)
        string_keys = [k for k in res.keys()
                       if isinstance(res[k], six.string_types)]
        obj_keys = [k for k in res.keys()
                    if isinstance(res[k], dict)]
        self.assertEqual(2, len(string_keys))
        self.assertEqual(1, len(obj_keys))
        obj = self._get_body(res[obj_keys[0]])
        self.assertEqual('FOO', obj['foo'])
        for ref_id in string_keys:
            self.assertEqual(res[obj_keys[0]]['id'], res[ref_id])

    def test_dump_with_meta_attributes(self):
        n1 = om.Object('dumptests.DumpTarget1', foo='FOO')
        n2 = om.Object('dumptests.DumpTarget1', foo='Bar')
        source = om.Object('dumptests.DumpTarget3', a=n1, b=n2)
        result = self._runner.testDump(source)
        res = self._get_body(result)
        self._get_body(res['a'])
        self.assertIsInstance(res['b'], six.string_types)

    def test_dump_with_inheritance(self):
        source = om.Object('dumptests.DumpTarget4', foo='FOO', qux='QUX')
        result = self._runner.testDump(source)
        res = self._get_body(result)
        self.assertEqual('FOO', res['foo'])
        self.assertEqual('QUX', res['qux'])

    def test_dump_with_inheritance_upcast_ignored(self):
        source = om.Object('dumptests.DumpTarget4', foo='FOO', qux='QUX')
        result = self._runner.testDumpWithUpcast(source, True, True)
        res = self._get_body(result)
        self.assertEqual('FOO', res['foo'])
        self.assertEqual('QUX', res['qux'])

    def test_dump_with_inheritance_upcast_allowed(self):
        source = om.Object('dumptests.DumpTarget4', foo='FOO', qux='QUX')
        result = self._runner.testDumpWithUpcast(source, True, False)
        res = self._get_body(result)
        self.assertEqual('FOO', res['foo'])
        self.assertNotIn('qux', res)

    def _get_body(self, obj):
        body_key = [k for k in obj.keys()
                    if k not in ('id', 'name', 'metadata')][0]
        self.assertIsInstance(body_key, dsl_types.MuranoType)
        return obj[body_key]
