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

import six

from murano.dsl import dsl
from murano.dsl import exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestContracts(test_case.DslTestCase):
    def setUp(self):
        super(TestContracts, self).setUp()
        self._runner = self.new_runner(
            om.Object(
                'ContractExamples',
                ordinaryProperty='PROPERTY',
                sampleClass=om.Object(
                    'SampleClass1',
                    stringProperty='string1',
                    classProperty=om.Object(
                        'SampleClass2',
                        class2Property='string2'))))

    def test_string_contract(self):
        result = self._runner.testStringContract('qwerty')
        self.assertIsInstance(result, six.string_types)
        self.assertEqual('qwerty', result)

    def test_string_from_number_contract(self):
        result = self._runner.testStringContract(123)
        self.assertIsInstance(result, six.string_types)
        self.assertEqual('123', result)

    def test_string_null_contract(self):
        self.assertIsNone(self._runner.testStringContract(None))

    def test_int_contract(self):
        result = self._runner.testIntContract(123)
        self.assertIsInstance(result, int)
        self.assertEqual(123, result)

    def test_int_from_string_contract(self):
        result = self._runner.testIntContract('456')
        self.assertIsInstance(result, int)
        self.assertEqual(456, result)

    def test_int_from_string_contract_failure(self):
        self.assertRaises(exceptions.ContractViolationException,
                          self._runner.testIntContract, 'nan')

    def test_int_null_contract(self):
        self.assertIsNone(self._runner.testIntContract(None))

    def test_bool_contract(self):
        result = self._runner.testBoolContract(True)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

        result = self._runner.testBoolContract(False)
        self.assertIsInstance(result, bool)
        self.assertFalse(result)

    def test_bool_from_int_contract(self):
        result = self._runner.testBoolContract(10)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

        result = self._runner.testBoolContract(0)
        self.assertIsInstance(result, bool)
        self.assertFalse(result)

    def test_bool_from_string_contract(self):
        result = self._runner.testBoolContract('something')
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

        result = self._runner.testBoolContract('')
        self.assertIsInstance(result, bool)
        self.assertFalse(result)

    def test_bool_null_contract(self):
        self.assertIsNone(self._runner.testIntContract(None))

    def test_class_contract(self):
        arg = om.Object('SampleClass2', class2Property='qwerty')
        result = self._runner.testClassContract(arg)
        self.assertIsInstance(result, dsl.MuranoObjectInterface)

    def test_class_contract_by_ref(self):
        arg = om.Object('SampleClass2', class2Property='qwerty')
        result = self._runner.testClassContract(arg)
        self.assertNotEqual(arg.id, result.id)

    def test_class_contract_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testClassContract, ['invalid type'])

    def test_class_contract_by_ref_failure(self):
        self.assertRaises(
            exceptions.NoObjectFoundError,
            self._runner.testClassContract, 'NoSuchIdExists')

    def test_class_contract_from_dict(self):
        self.assertEqual(
            'SampleClass2',
            self._runner.testClassContract({
                'class2Property': 'str'}).type.name)

    def test_class_from_id_contract(self):
        object_id = self._runner.root.get_property('sampleClass').object_id
        result = self._runner.testClassFromIdContract(object_id)
        self.assertIsInstance(result, dsl.MuranoObjectInterface)
        self.assertEqual(object_id, result.id)

    def test_template_contract(self):
        arg = om.Object('CreatedClass2', property1='qwerty', property2=123)
        result = self._runner.testTemplateContract(arg)
        self.assertIsInstance(result, dict)
        self.assertItemsEqual(['?', 'property1', 'property2'], result.keys())

    def test_template_property_contract(self):
        template = {
            'foo': 123
        }
        self.new_runner(
            om.Object('ContractExamples', templateProperty=template))

    def test_template_contract_fail_on_type(self):
        arg = om.Object('SampleClass2', class2Property='qwerty')
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testTemplateContract, arg)

    def test_template_contract_with_property_exclusion(self):
        arg = om.Object('CreatedClass2', property1='qwerty',
                        property2='INVALID')
        result = self._runner.testTemplateContractExcludeProperty(arg)
        self.assertIsInstance(result, dict)
        self.assertItemsEqual(['?', 'property1'], result.keys())

    def test_template_contract_with_property_exclusion_from_mpl(self):
        result = self._runner.testTemplateContractExcludePropertyFromMpl()
        self.assertIsInstance(result, dict)
        self.assertItemsEqual(['?', 'property1'], result.keys())

    def test_check_contract(self):
        arg = om.Object('SampleClass2', class2Property='qwerty')
        self.assertIsNone(self._runner.testCheckContract(arg, 100))

    def test_check_contract_failure(self):
        invalid_arg = om.Object('SampleClass2', class2Property='not qwerty')
        self.assertRaises(exceptions.ContractViolationException,
                          self._runner.testCheckContract, invalid_arg, 100)

    def test_owned_contract(self):
        arg1 = self._runner.root.get_property('sampleClass')
        arg2 = arg1.get_property('classProperty')
        self.assertIsNone(self._runner.testOwnedContract(arg1, arg2))

    def test_owned_contract_on_null(self):
        self.assertIsNone(self._runner.testOwnedContract(None, None))

    def test_owned_contract_failure(self):
        arg1 = self._runner.root.get_property('sampleClass')
        arg2 = arg1.get_property('classProperty')
        invalid_arg2 = om.Object('SampleClass2', class2Property='string2')
        invalid_arg1 = om.Object(
            'SampleClass1',
            stringProperty='string1',
            classProperty=invalid_arg2)

        self.assertRaises(exceptions.ContractViolationException,
                          self._runner.testOwnedContract, invalid_arg1, arg2)
        self.assertRaises(exceptions.ContractViolationException,
                          self._runner.testOwnedContract, invalid_arg2, arg1)

    def test_not_owned_contract(self):
        arg2 = om.Object('SampleClass2', class2Property='string2')
        arg1 = om.Object(
            'SampleClass1',
            stringProperty='string1',
            classProperty=arg2)
        self.assertIsNone(self._runner.testNotOwnedContract(arg1, arg2))

    def test_not_owned_contract_on_null(self):
        self.assertIsNone(self._runner.testNotOwnedContract(None, None))

    def test_not_owned_contract_failure(self):
        invalid_arg1 = self._runner.root.get_property('sampleClass')
        invalid_arg2 = invalid_arg1.get_property('classProperty')
        arg2 = om.Object('SampleClass2', class2Property='string2')
        arg1 = om.Object(
            'SampleClass1',
            stringProperty='string1',
            classProperty=arg2)

        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testNotOwnedContract, invalid_arg1, arg2)
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testNotOwnedContract, invalid_arg2, arg1)

    def test_scalar_contract(self):
        self.assertEqual('fixed', self._runner.testScalarContract(
            'fixed', 456, True))

    def test_scalar_contract_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testScalarContract,
            'wrong', 456, True)

        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testScalarContract,
            'fixed', 123, True)

        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testScalarContract,
            'fixed', 456, False)

    def test_list_contract(self):
        self.assertEqual([3, 2, 1], self._runner.testListContract(
            ['3', 2, '1']))

    def test_list_contract_from_scalar(self):
        self.assertEqual([99], self._runner.testListContract('99'))

    def test_list_contract_from_null(self):
        self.assertEqual([], self._runner.testListContract(None))

    def test_list_with_min_length_contract(self):
        self.assertEqual(
            [1, 2, 3],
            self._runner.testListWithMinLengthContract([1, 2, 3]))
        self.assertEqual(
            [1, 2, 3, 4],
            self._runner.testListWithMinLengthContract([1, 2, 3, 4]))

    def test_list_with_min_length_contract_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testListWithMinLengthContract, None)
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testListWithMinLengthContract, [1, 2])

    def test_list_with_min_max_length_contract(self):
        self.assertEqual(
            [1, 2],
            self._runner.testListWithMinMaxLengthContract([1, 2]))
        self.assertEqual(
            [1, 2, 3, 4],
            self._runner.testListWithMinMaxLengthContract([1, 2, 3, 4]))

    def test_list_with_min_max_length_contract_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testListWithMinMaxLengthContract, [1])
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testListWithMinMaxLengthContract, [1, 2, 3, 4, 5])

    def test_dict_contract(self):
        self.assertEqual(
            {'A': '123', 'B': 456},
            self._runner.testDictContract({'A': '123', 'B': '456'}))
        self.assertEqual(
            {'A': '123', 'B': 456},
            self._runner.testDictContract({'A': '123', 'B': '456', 'C': 'qq'}))
        self.assertEqual(
            {'A': '123', 'B': None},
            self._runner.testDictContract({'A': '123'}))

    def test_dict_contract_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testDictContract, 'str')

    def test_dict_expressions_contract(self):
        self.assertEqual(
            {321: 'qwerty', 99: 'val', 'B': 456},
            self._runner.testDictExprContract({
                '321': 'qwerty', '99': 'val', 'B': 456}))

    def test_dict_expressions_contract_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testDictExprContract,
            {'321': 'qwerty', 'str': 'val', 'B': 456})

    def test_invalid_dict_expr_contract(self):
        self.assertRaises(
            exceptions.DslContractSyntaxError,
            self._runner.testDictMultiExprContract,
            {'321': 'qwerty', 'str': 'val', 'B': 456})

    def test_not_null_contract(self):
        self.assertEqual('value', self._runner.testNotNullContract('value'))

    def test_not_null_contract_failure(self):
        self.assertRaises(
            exceptions.ContractViolationException,
            self._runner.testNotNullContract, None)

    def test_default(self):
        self.assertEqual('value', self._runner.testDefault('value'))
        self.assertEqual('DEFAULT', self._runner.testDefault())

    def test_default_expression(self):
        self.assertEqual('PROPERTY', self._runner.testDefaultExpression())
        self.assertEqual('value', self._runner.testDefaultExpression('value'))

    def test_template_with_externally_owned_object(self):
        node = om.Object('Node', 'OBJ_ID')
        node_template = om.Object('Node', nodes=['OBJ_ID'])
        model = om.Object(
            'TemplatePropertyClass', owned=node, template=node_template)
        runner = self.new_runner(model)
        self.assertEqual(
            ['OBJ_ID'], runner.testTemplateWithExternallyOwnedObject())


class TestContractsTransform(test_case.DslTestCase):
    def setUp(self):
        super(TestContractsTransform, self).setUp()
        self._runner = self.new_runner(om.Object('TestIteratorsTransform'))

    def test_property(self):
        self.assertEqual('3', self._runner.testProperties())

    def test_argument(self):
        self.assertEqual('3', self._runner.testArgs())
        self.assertEqual('2', self._runner.testUntypedArgs())
        self.assertEqual('6', self._runner.testNotTypedListArgs())
        self.assertEqual('6', self._runner.testTypedList())
        self.assertEqual(2, self._runner.testListDict())
