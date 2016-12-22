# Copyright (c) 2015 Mirantis, Inc.
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


class TestCall(test_case.DslTestCase):
    def setUp(self):
        super(TestCall, self).setUp()
        self._runner = self.new_runner(om.Object('TestCall'))

    def test_call(self):
        self._runner.testCall()
        self.assertEqual(['called as call'], self._traces)

    def test_method(self):
        self._runner.testMethodInvocation()
        self.assertEqual(['called as method'], self._traces)

    def test_call_static(self):
        self._runner.testCallStatic()
        self.assertEqual(['called as static'], self._traces)

    def test_call_static_as_instance(self):
        self._runner.testCallStaticAsInstance()
        self.assertEqual(['called as static'], self._traces)
