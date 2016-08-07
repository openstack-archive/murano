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
from testtools import matchers

from murano.dsl import serializer
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


# Tests for correctness of serialization of MuranoPL object tree
# back to Object Model

class TestResultsSerializer(test_case.DslTestCase):
    def setUp(self):
        super(TestResultsSerializer, self).setUp()
        self._class2 = om.Object('SampleClass2',
                                 class2Property='string2')
        self._class1 = om.Object(
            'SampleClass1', 'def',
            stringProperty='string1',
            arbitraryProperty={'a': [1, 2]},
            classProperty=self._class2)
        self._root_class = om.Object('ContractExamples', 'abc',
                                     sampleClass=self._class1)

        self._runner = self.new_runner(self._root_class)

    def _test_data_in_section(self, name, serialized):
        """Test that Model -> Load -> Serialize = Model

        Test that a section of Object Model has expected structure and
           property values that are equal to those originally loaded
           (e.g. that Model -> Load -> Serialize = Model)

           :param name: section name
           :param serialized: serialized Object Model
        """

        self.assertEqual('abc',
                         serialized[name]['?']['id'])
        self.assertEqual('ContractExamples/0.0.0@tests',
                         serialized['Objects']['?']['type'])
        self.assertIsInstance(serialized[name]['sampleClass'], dict)
        self.assertEqual('def',
                         serialized[name]['sampleClass']['?']['id'])
        self.assertEqual('SampleClass1/0.0.0@tests',
                         serialized[name]['sampleClass']['?']['type'])
        self.assertEqual('string1',
                         serialized[name]['sampleClass']['stringProperty'])

    def test_results_serialize(self):
        """Test that serialized contains same values and headers

        Test that serialized Object Model has both Objects and ObjectsCopy
        sections and they both contain the same property values and object
        headers. Note, that Objects section may contain additional designer
        metadata and information on available actions that is not needed in
        ObjectsCopy thus we cannot test for ObjectsCopy be strictly equal to
        Objects
        """

        serialized = self._runner.serialized_model
        self.assertIn('Objects', serialized)
        self.assertIn('ObjectsCopy', serialized)
        self._test_data_in_section('Objects', serialized)
        self._test_data_in_section('ObjectsCopy', serialized)

    def test_actions(self):
        """Test that information on actions can be invoked

        Test that information on actions can be invoked on each MuranoPL
        object are persisted into object header ('?' key) during serialization
        of Objects section of Object Model

        """
        serialized = self._runner.serialized_model
        actions = serialized['Objects']['?'].get('_actions')
        self.assertIsInstance(actions, dict)
        action_names = [action['name'] for action in actions.values()]
        self.assertIn('testAction', action_names)
        self.assertNotIn('notAction', action_names)
        self.assertIn('testRootMethod', action_names)
        action_meta = None
        for action in actions.values():
            self.assertIsInstance(action.get('enabled'), bool)
            self.assertIsInstance(action.get('name'), six.string_types)
            self.assertThat(
                action['name'],
                matchers.StartsWith('test'))
            if action['name'] == 'testActionMeta':
                action_meta = action
            else:
                self.assertEqual(action['title'], action['name'])
        self.assertIsNotNone(action_meta)
        self.assertEqual(action_meta['title'], "Title of the method")
        self.assertEqual(action_meta['description'],
                         "Description of the method")
        self.assertEqual(action_meta['helpText'], "HelpText of the method")

    def test_attribute_serialization(self):
        """Test that attributes produced by MuranoPL code are persisted

        Test that attributes produced by MuranoPL code are persisted in
        dedicated section of Object Model. Attributes are values that are
        stored in special key-value storage that is private to each class.
        Classes can store state data there. Attributes are persisted across
        deployment sessions but are not exposed via API (thus cannot be
        accessed by dashboard)
        """

        self._runner.on(self._class1).testAttributes('VALUE')
        serialized = self._runner.serialized_model
        self.assertIsInstance(serialized.get('Attributes'), list)
        self.assertThat(
            serialized['Attributes'],
            matchers.HasLength(1))
        self.assertEqual(
            [self._class1.id, 'SampleClass1', 'att1', 'VALUE'],
            serialized['Attributes'][0])

    def test_attribute_deserialization(self):
        """Test that attributes are available

        Test that attributes that are put into Attributes section of
        Object Model become available to appropriate MuranoPL classes
        """

        serialized = self._runner.serialized_model
        serialized['Attributes'].append(
            [self._class1.id, 'SampleClass1', 'att2', ' Snow'])
        runner2 = self.new_runner(serialized)
        self.assertEqual(
            'John Snow',
            runner2.on(self._class1).testAttributes('John'))

    def test_value_deserialization(self):
        """Test serialization of arbitrary values

        Test serialization of arbitrary values that can be returned
        from action methods
        """

        runner = self.new_runner(self._class2)
        result = runner.testMethod()
        self.assertEqual(
            {
                'key1': 'abc',
                'key2': ['a', 'b', 'c'],
                'key3': None,
                'key4': False,
                'key5': {'x': 'y'},
                'key6': [{'w': 'q'}]
            },
            serializer.serialize(result, runner.executor))
