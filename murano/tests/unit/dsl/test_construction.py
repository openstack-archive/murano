# Copyright (c) 2014 Mirantis, Inc.
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

from murano.dsl import dsl
from murano.dsl import serializer
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestConstruction(test_case.DslTestCase):
    def setUp(self):
        super(TestConstruction, self).setUp()
        self._runner = self.new_runner(om.Object('CreatingClass'))

    def test_new(self):
        self._runner.testNew()
        self.assertEqual(
            ['CreatingClass::.init', 'CreatedClass1::.init',
             'string', 'STRING', 123],
            self.traces)

    def test_new_with_ownership(self):
        obj = serializer.serialize(self._runner.testNewWithOwnership(),
                                   self._runner.executor, allow_refs=False)
        self.assertEqual('STRING', obj.get('property1'))
        self.assertIsNotNone('string', obj.get('xxx'))
        self.assertEqual('STR', obj['xxx'].get('property1'))
        self.assertEqual('QQQ', obj['xxx']['?'].get('name'))

    def test_new_with_dict(self):
        self._runner.testNewWithDict()
        self.assertEqual(
            ['CreatingClass::.init', 'CreatedClass1::.init',
             'string', 'STRING', 123],
            self.traces)

    def test_model_load(self):
        res = self._runner.testLoadCompexModel()
        for i in range(3):
            self.assertThat(res[i], matchers.Not(matchers.Contains('node')))
        self.assertEqual(self._runner.root.object_id, res[3])
        self.assertEqual(
            [
                'rootNode',
                ['childNode1', 'childNode2', 'childNode2'],
                True, True, True, True, True,
                'rootNode', 'childNode2', 'childNode1'
            ], res[4:])

    def test_single_contract_instantiation(self):
        self._runner.testSingleContractInstantiation()
        self.assertEqual(1, self.traces.count('ConstructionSample::init'))

    def test_nested_new_loads_in_separate_store(self):
        res = self._runner.testNestedNewLoadsInSeparateStore()
        self.assertIsInstance(res, dsl.MuranoObjectInterface)

    def test_reference_access_from_init(self):
        self._runner.testReferenceAccessFromInit()
        self.assertEqual(2, self.traces.count('childNode'))
