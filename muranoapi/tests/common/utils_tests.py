#    Copyright (c) 2013 Mirantis, Inc.
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
import unittest2 as unittest
from muranoapi.common.utils import auto_id


class AutoIdTests(unittest.TestCase):
    def test_simple_dict(self):
        source = {"attr": True}
        value = auto_id(source)
        self.assertIn('id', value)

    def test_nested_lists(self):
        source = {"attr": True, "obj": {"attr": False}}
        value = auto_id(source)
        self.assertIn('id', value)

    def test_list_with_ints(self):
        source = [0, 1, 2, 3]
        value = auto_id(source)
        self.assertListEqual(value, source)

    def test_list_with_dicts(self):
        source = [{"attr": True}, {"attr": False}]
        value = auto_id(source)
        for item in value:
            self.assertIn('id', item)
