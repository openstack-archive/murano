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

from murano.common.helpers import token_sanitizer
from murano.tests.unit import base


class TokenSanitizerTests(base.MuranoTestCase):
    sanitizer = token_sanitizer.TokenSanitizer()

    def test_dict_with_one_value(self):
        source = {'token': 'value'}
        value = self.sanitizer.sanitize(source)
        self.assertEqual(value['token'], self.sanitizer.message)

    def test_dict_with_few_value(self):
        source = {'token': 'value', 'pass': 'value', 'TrustId': 'value'}
        value = self.sanitizer.sanitize(source)

        self.assertEqual(value['token'], self.sanitizer.message)
        self.assertEqual(value['pass'], self.sanitizer.message)
        self.assertEqual(value['TrustId'], self.sanitizer.message)

    def test_dict_with_nested_dict(self):
        source = {'obj': {'pass': 'value'}}
        value = self.sanitizer.sanitize(source)
        self.assertEqual(value['obj']['pass'], self.sanitizer.message)

    def test_dict_with_nested_list(self):
        source = {'obj': [{'pass': 'value'}]}
        value = self.sanitizer.sanitize(source)
        self.assertEqual(value['obj'][0]['pass'], self.sanitizer.message)

    def test_leave_out_other_values(self):
        source = {'obj': ['value']}
        value = self.sanitizer.sanitize(source)
        self.assertEqual(value['obj'][0], 'value')
