# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import semantic_version

from murano.dsl import helpers
from murano.tests.unit import base


class TestMergeDicts(base.MuranoTestCase):
    def check(self, dict1, dict2, expected):
        result = helpers.merge_dicts(dict1, dict2)
        self.assertEqual(expected, result)

    def test_dicts_plain(self):
        dict1 = {"a": "1"}
        dict2 = {"a": "100", "ab": "12"}
        expected = {"a": "100", "ab": "12"}
        self.check(dict1, dict2, expected)

    def test_different_types_none(self):
        dict1 = {"a": "1"}
        dict2 = {"a": None, "ab": "12"}
        expected = {"a": "1", "ab": "12"}
        self.check(dict1, dict2, expected)

    def test_different_types_of_iterable(self):
        dict1 = {"a": {"ab": "1"}}
        dict2 = {"a": ["ab", "1"]}
        self.assertRaises(TypeError, helpers.merge_dicts, dict1, dict2)

    def test_merge_nested_dicts(self):
        dict1 = {"a": {"ab": {}, "abc": "1"}}
        dict2 = {"a": {"abc": "123"}}
        expected = {"a": {"ab": {}, "abc": "123"}}
        self.check(dict1, dict2, expected)

    def test_merge_nested_dicts_with_max_levels(self):
        dict1 = {"a": {"ab": {"abcd": "1234"}, "abc": "1"}}
        dict2 = {"a": {"ab": {"y": "9"}, "abc": "123"}}
        expected = {"a": {"ab": {"y": "9"}, "abc": "123"}}
        result = helpers.merge_dicts(dict1, dict2, max_levels=2)
        self.assertEqual(expected, result)

    def test_merge_with_lists(self):
        dict1 = {"a": [1, 2]}
        dict2 = {"a": [1, 3, 2, 4]}
        expected = {"a": [1, 2, 3, 4]}
        self.check(dict1, dict2, expected)


class TestParseVersionSpec(base.MuranoTestCase):
    def check(self, expected, version_spec):
        self.assertEqual(expected, helpers.parse_version_spec(version_spec))

    def test_empty_version_spec(self):
        version_spec = ""
        expected = semantic_version.Spec('>=0.0.0', '<1.0.0-0')
        self.check(expected, version_spec)

    def test_empty_kind(self):
        version_spec = "1.11.111"
        expected = semantic_version.Spec('==1.11.111')
        self.check(expected, version_spec)

    def test_implicit_major(self):
        version_spec = ">=2"
        expected = semantic_version.Spec('>=2.0.0')
        self.check(expected, version_spec)

    def test_implicit_minor(self):
        version_spec = ">=2.1"
        expected = semantic_version.Spec('>=2.1.0')
        self.check(expected, version_spec)

    def test_remove_spaces(self):
        version_spec = "< =  2 .1"
        expected = semantic_version.Spec('<2.2.0-0')
        self.check(expected, version_spec)

    def test_input_version(self):
        version_spec = semantic_version.Version('1.11.111')
        expected = semantic_version.Spec('==1.11.111')
        self.check(expected, version_spec)

    def test_input_spec(self):
        version_spec = semantic_version.Spec('<=1', '<=1.11')
        expected = semantic_version.Spec('<1.12.0-0', '<2.0.0-0')
        self.check(expected, version_spec)
