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

from murano.dsl import exceptions
from murano.dsl.principal_objects import garbage_collector
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestGC(test_case.DslTestCase):
    def setUp(self):
        super(TestGC, self).setUp()

        self.package_loader.load_package('io.murano', None).register_class(
            garbage_collector.GarbageCollector)
        self.runner = self.new_runner(om.Object('TestGC'))

    def test_model_destroyed(self):
        model = om.Object(
            'TestGCNode', 'root',
            value='root',
            nodes=[
                om.Object(
                    'TestGCNode', 'node1',
                    value='node1',
                    nodes=['root', 'node2']
                ),
                om.Object(
                    'TestGCNode', 'node2',
                    value='node2',
                    nodes=['root', 'node1']
                ),
            ]
        )
        model = {'Objects': None, 'ObjectsCopy': model}
        self.new_runner(model)
        self.assertItemsEqual(['node1', 'node2'], self.traces[:2])
        self.assertEqual('root', self.traces[-1])

    def test_collect_from_code(self):
        self.runner.testObjectsCollect()
        self.assertEqual(['B', 'A'], self.traces)

    def test_collect_with_subscription(self):
        self.runner.testObjectsCollectWithSubscription()
        self.assertEqual(
            ['Destroy A', 'Destroy B', 'Destruction of B', 'B', 'A'],
            self.traces)

    def test_call_on_destroyed_object(self):
        self.assertRaises(
            exceptions.ObjectDestroyedError,
            self.runner.testCallOnDestroyedObject)
        self.assertEqual(['foo', 'X'], self.traces)

    def test_destruction_dependencies_serialization(self):
        self.runner.testDestructionDependencySerialization()
        node1 = self.runner.serialized_model['Objects']['outNode']
        node2 = node1['nodes'][0]

        deps = {
            'onDestruction': [{
                'subscriber': self.runner.root.object_id,
                'handler': '_handler'
            }]
        }
        self.assertEqual(deps, node1['?'].get('dependencies'))

        self.assertEqual(
            node1['?'].get('dependencies'),
            node2['?'].get('dependencies'))

        model = self.runner.serialized_model
        model['Objects']['outNode'] = None
        self.new_runner(model)
        self.assertEqual(['Destroy A', 'Destroy B', 'B', 'A'], self.traces)

    def test_is_doomed(self):
        self.runner.testIsDoomed()
        self.assertEqual([[], True, 'B', [True], False, 'A'], self.traces)

    def test_is_destroyed(self):
        self.runner.testIsDestroyed()
        self.assertEqual([False, True], self.traces)

    def test_static_property_not_destroyed(self):
        self.runner.testStaticProperties()
        self.assertEqual([], self.traces)

    def test_args_not_destroyed(self):
        self.runner.testDestroyArgs()
        self.assertEqual([], self.traces)

    def test_runtime_property_not_destroyed(self):
        self.runner.testReachableRuntimeProperties()
        self.assertEqual([False, ], self.traces)
