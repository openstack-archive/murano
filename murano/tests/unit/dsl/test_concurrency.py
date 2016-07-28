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

import eventlet


from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestConcurrency(test_case.DslTestCase):
    def setUp(self):
        super(TestConcurrency, self).setUp()

        def yield_():
            self.traces.append('yield')
            eventlet.sleep(0)

        self.register_function(yield_, 'yield')
        self._runner = self.new_runner(om.Object('TestConcurrency'))

    def check_isolated_traces(self):
        for i in range(0, len(self.traces), 3):
            before = self.traces[i]
            switch = self.traces[i+1]
            after = self.traces[i+2]
            self.assertEqual('yield', switch)
            self.assertEqual(before[0:6], after[0:6])
            self.assertTrue(before.endswith('-before'))
            self.assertTrue(after.endswith('-after'))

    def check_concurrent_traces(self):
        self.assertTrue(self.traces[0].endswith('-before'))
        self.assertEqual('yield', self.traces[1])
        self.assertTrue(self.traces[2].endswith('-before'))
        self.assertEqual('yield', self.traces[3])
        self.assertTrue(self.traces[4].endswith('-before'))
        self.assertEqual('yield', self.traces[5])
        self.assertTrue(self.traces[6].endswith('-after'))
        self.assertTrue(self.traces[7].endswith('-after'))
        self.assertTrue(self.traces[8].endswith('-after'))

    def test_isolated(self):
        self._runner.testCallIsolated()
        self.check_isolated_traces()

    def test_isolated_default(self):
        self._runner.testCallIsolatedWithDefault()
        self.check_isolated_traces()

    def test_concurrent_explicit(self):
        self._runner.testCallConcurrentExplicit()
        self.check_concurrent_traces()

    def test_isolated_explicit(self):
        self._runner.testCallIsolatedExplicit()
        self.check_isolated_traces()

    def test_argbased_primitive_isolated(self):
        self._runner.testCallArgbasedPrimitiveIsolated()
        self.check_isolated_traces()

    def test_argbased_primitive_concurrent(self):
        self._runner.testCallArgbasedPrimitiveConcurrent()
        self.check_concurrent_traces()

    def test_argbased_object_isolated(self):
        self._runner.testCallArgbasedWithObjectIsolated()
        self.check_isolated_traces()

    def test_argbased_object_concurrent(self):
        self._runner.testCallArgbasedWithObjectConcurrent()
        self.check_concurrent_traces()
