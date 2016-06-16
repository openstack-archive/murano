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
                                   self._runner.executor)
        self.assertEqual('STRING', obj.get('property1'))
        self.assertIsNotNone('string', obj.get('xxx'))
        self.assertEqual('STR', obj['xxx'].get('property1'))
        self.assertEqual('QQQ', obj['xxx']['?'].get('name'))
