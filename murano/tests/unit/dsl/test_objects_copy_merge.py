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

import copy

from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestObjectsCopyMerge(test_case.DslTestCase):
    def test_merged(self):
        gen1_model = om.Object(
            'TestObjectsCopyMergeSampleClass', 'rootNode',
            value='node1',
            nodes=[
                om.Object('TestObjectsCopyMergeSampleClass',
                          value='node2',
                          nodes=[om.Ref('rootNode')])
            ])

        gen2_model = copy.deepcopy(gen1_model)
        gen2_model['nodes'] = []
        gen2_model['value'] = 'node1-updated'

        model = {
            'Objects': gen2_model,
            'ObjectsCopy': gen1_model
        }

        runner = self.new_runner(model)
        self.assertEqual(['node2', 'node1-updated'], self.traces)
        self.assertEqual('It works!', runner.testMethod())
