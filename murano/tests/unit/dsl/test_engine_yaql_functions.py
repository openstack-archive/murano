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

import mock
import six
from testtools import matchers
from yaql.language import exceptions as yaql_exceptions

from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case

from castellan.common import exception as castellan_exception


class TestEngineYaqlFunctions(test_case.DslTestCase):
    def setUp(self):
        super(TestEngineYaqlFunctions, self).setUp()
        self._runner = self.new_runner(om.Object('TestEngineFunctions'))

    def test_join(self):
        self.assertEqual('xx 123', self._runner.testJoin())

    def test_split(self):
        self.assertEqual(
            ['x', 'yy', '123'],
            self._runner.testSplit())

    def test_len(self):
        self.assertEqual(8, self._runner.testLen())

    def test_coalesce(self):
        self.assertEqual('a', self._runner.testCoalesce('a', 'b', 'c'))
        self.assertEqual('b', self._runner.testCoalesce(None, 'b', 'c'))
        self.assertEqual('c', self._runner.testCoalesce(None, None, 'c'))

    def test_base64(self):
        encoded = 'VEVTVA=='
        self.assertEqual(
            encoded,
            self._runner.testBase64Encode('TEST'))
        self.assertEqual(
            'TEST',
            self._runner.testBase64Decode(encoded))

    def test_format(self):
        self.assertEqual(
            '2 + 3',
            self._runner.testFormat('{0} + {1}', 2, 3))

    def test_replace_str(self):
        self.assertEqual(
            'John Doe',
            self._runner.testReplaceStr('John Kennedy', 'Kennedy', 'Doe'))

        self.assertRaises(
            yaql_exceptions.NoMatchingMethodException,
            self._runner.testReplaceStr, None, 'Kennedy', 'Doe')

    def test_replace_dict(self):
        self.assertEqual(
            'Marilyn Monroe',
            self._runner.testReplaceDict('John Kennedy', {
                'John': 'Marilyn',
                'Kennedy': 'Monroe'
            }))

    def test_lower(self):
        self.assertEqual(
            'test',
            self._runner.testToLower('TESt'))

    def test_upper(self):
        self.assertEqual(
            'TEST',
            self._runner.testToUpper('tEst'))

    def test_starts_with(self):
        self.assertIs(
            True,
            self._runner.testStartsWith('TEST', 'TE'))
        self.assertIs(
            False,
            self._runner.testStartsWith('TEST', 'te'))

    def test_ends_with(self):
        self.assertIs(
            True,
            self._runner.testEndsWith('TEST', 'ST'))
        self.assertIs(
            False,
            self._runner.testEndsWith('TEST', 'st'))

    def test_trim(self):
        self.assertEqual(
            'test',
            self._runner.testTrim('\n\t test \t\n'))

    def test_substr(self):
        self.assertEqual(
            'teststr',
            self._runner.testSubstr('teststr', 2, 3))

    def test_str(self):
        self.assertEqual(
            '123',
            self._runner.testStr(123))
        self.assertEqual(
            'true',
            self._runner.testStr(True))
        self.assertEqual(
            'false',
            self._runner.testStr(False))
        self.assertEqual(
            'null',
            self._runner.testStr(None))

    def test_int(self):
        self.assertEqual(
            123,
            self._runner.testInt('123'))
        self.assertEqual(
            0,
            self._runner.testInt(None))

    def test_keys(self):
        self.assertThat(
            self._runner.testKeys({True: 123, 5: 'Q', 'y': False}),
            matchers.MatchesSetwise(
                matchers.Equals('y'),
                matchers.Is(True),
                matchers.Equals(5)))

    def test_values(self):
        self.assertThat(
            self._runner.testValues({True: 123, 5: 'Q', 'y': False}),
            matchers.MatchesSetwise(
                matchers.Is(False),
                matchers.Equals(123),
                matchers.Equals('Q')))

    def test_flatten(self):
        self.assertEqual(
            [1, 2, 3, 4],
            self._runner.testFlatten([[1, 2], [3, 4]]))

    def test_dict_get(self):
        self.assertEqual(
            2,
            self._runner.testDictGet({'a': 'x', 'y': 2}, 'y'))

    def test_random_name(self):
        name1 = self._runner.testRandomName()
        name2 = self._runner.testRandomName()

        self.assertIsInstance(name1, six.string_types)
        self.assertIsInstance(name2, six.string_types)
        self.assertThat(len(name1), matchers.GreaterThan(12))
        self.assertThat(len(name2), matchers.GreaterThan(12))
        self.assertThat(name1, matchers.NotEquals(name2))

    def test_pselect(self):
        self.assertEqual(
            [1, 4, 9, 16, 25, 36, 49, 64, 81, 100],
            self._runner.testPSelect([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

    def test_bind(self):
        self.assertEqual(
            {
                'a': 5,
                'b': True,
                'c': {
                    'd': 'x'
                },
                'e': ['qq-123']
            },
            self._runner.testBind(
                {
                    'a': '$a',
                    '$Z': True,
                    'c': {
                        'd': '$value of d'
                    },
                    'e': ['$qq-{suffix}']
                },
                {'a': 5, 'Z': 'b', 'value of d': 'x', 'suffix': 123}))

    def test_patch(self):
        self.assertEqual(
            {'foo': 'bar', 'baz': [42]},
            self._runner.testPatch())

    def test_skip(self):
        self.assertEqual(
            [3, 4, 5, 6],
            self._runner.testSkip([1, 2, 3, 4, 5, 6], 2)
        )

    def test_take(self):
        self.assertEqual(
            [1, 2, 3],
            self._runner.testTake([1, 2, 3, 4, 5, 6], 3)
        )

    def test_skip_take(self):
        self.assertEqual(
            [3, 4, 5],
            self._runner.testSkipTake([1, 2, 3, 4, 5, 6, 7, 8],
                                      2, 3)
        )

    def test_skip_take_chained(self):
        self.assertEqual(
            [3, 4, 5],
            self._runner.testSkipTakeChained(
                [1, 2, 3, 4, 5, 6, 7, 8],
                2, 3)
        )

    def test_aggregate(self):
        self.assertEqual(
            10,
            self._runner.testAggregate([1, 2, 3, 4])
        )

    def test_aggregate_with_initializer(self):
        self.assertEqual(
            21,
            self._runner.testAggregateWithInitializer([1, 2, 3, 4], 11)
        )

    def test_id(self):
        obj_id = self._runner.root.object_id
        self.assertEqual(obj_id * 2, self._runner.testId())

    def test_type(self):
        self.assertEqual('TestEngineFunctions' * 2, self._runner.testType())

    def test_is_operator(self):
        self.assertTrue(self._runner.testIsOperator())
        self.assertFalse(self._runner.testNegativeIsOperator())

    def test_new_object_assignment(self):
        self.assertTrue(self._runner.testNewObjectAssignment())

    @mock.patch('murano.engine.system.yaql_functions.key_manager')
    @mock.patch('murano.engine.system.yaql_functions.castellan_utils')
    def test_decrypt_data(self, mock_castellan_utils, mock_key_manager):
        dummy_context = mock.MagicMock()
        mock_castellan_utils.credential_factory.return_value = dummy_context

        encrypted_value = '91f784d0-5ef1-4b6f-9311-9b5a33d828d8'
        decrypted_value = 'secret_password'

        mock_key_manager.API().get.return_value.get_encoded.return_value =\
            decrypted_value
        self.assertEqual(decrypted_value,
                         self._runner.testDecryptData(encrypted_value))
        mock_key_manager.API().get.assert_called_once_with(dummy_context,
                                                           encrypted_value)

    @mock.patch('murano.engine.system.yaql_functions.LOG')
    def test_decrypt_data_not_configured(self, mock_log):
        encrypted_value = '91f784d0-5ef1-4b6f-9311-9b5a33d828d8'
        self.assertRaises(castellan_exception.AuthTypeInvalidError,
                          self._runner.testDecryptData, encrypted_value)
        mock_log.error.assert_called()
