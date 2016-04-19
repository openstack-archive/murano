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

from yaql.language import exceptions as yaql_exceptions

from murano.dsl import exceptions as dsl_exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestMethodParamInheritance(test_case.DslTestCase):
    def setUp(self):
        super(TestMethodParamInheritance, self).setUp()
        model = om.Object('TestMethodParamInheritanceDerived')
        self._runner = self.new_runner(model)

    def test_different_set_of_params_causes_exception(self):

        self.assertRaises(
            yaql_exceptions.NoMatchingMethodException,
            self._runner.testRunWithParam)
        self.assertRaises(
            dsl_exceptions.ContractViolationException,
            self._runner.testRunWithoutParam)
