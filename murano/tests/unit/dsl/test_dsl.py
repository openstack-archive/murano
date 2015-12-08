# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

from yaql.language import exceptions as yaql_exc
from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions as dsl_exc
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


@specs.parameter('param1', dsl.OneOf(dsl.MuranoTypeName(),
                                     dsl_types.MuranoObject))
@specs.parameter('param2', dsl.OneOf(yaqltypes.NumericConstant(),
                                     yaqltypes.BooleanConstant(),
                                     nullable=True))
def test_one_of(param1, param2):
    return 'Passed'


class TestOneOf(test_case.DslTestCase):
    def setUp(self):
        super(TestOneOf, self).setUp()

        self.register_function(test_one_of, 'testOneOf')
        self.runner = self.new_runner(om.Object('OneOfSmartType'))

    def test_negative(self):
        self.assertRaises(yaql_exc.NoMatchingFunctionException,
                          self.runner.testNegative1)
        self.assertRaises(dsl_exc.NoClassFound, self.runner.testNegative2)
        self.assertRaises(yaql_exc.NoMatchingFunctionException,
                          self.runner.testNegative3)

    def test_nullable(self):
        self.runner.testNullable()
        self.assertEqual(['Passed'], self.traces)

    def test_positive(self):
        self.runner.testPositive1()
        self.runner.testPositive2()
        self.runner.testPositive3()

        self.assertEqual(['Passed', 'Passed', 'Passed'], self.traces)
