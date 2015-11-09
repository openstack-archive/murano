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

from murano.dsl import helpers
from murano.tests.unit import base


class TestHeatStack(base.MuranoTestCase):
    def test_merge_dicts(self):
        dict1 = {"resource": "test"}
        dict2 = {"description": "Test merge dicts"}
        result = helpers.merge_dicts(dict1, dict2)
        expected = {"resource": "test",
                    "description": "Test merge dicts"}
        self.assertEqual(expected, result)

        dict2 = {"resource": None, "description": "Test merge dicts"}
        result = helpers.merge_dicts(dict1, dict2)
        expected = {"resource": "test",
                    "description": "Test merge dicts"}
        self.assertEqual(expected, result)

        dict2 = {"resource": "abc", "description": "Test merge dicts"}
        self.assertEqual(expected, result)

        dict2 = {"resource": {"test": 1}}
        self.assertRaises(TypeError, helpers.merge_dicts, dict1, dict2)

        dict1 = {"resource": None}
        dict2 = {"resource": "test", "description": "Test merge dicts"}
        expected = {"resource": None, "description": "Test merge dicts"}
        result = helpers.merge_dicts(dict1, dict2)
        self.assertEqual(expected, result)
