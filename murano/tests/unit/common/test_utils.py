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

from murano.common import utils
from murano.tests.unit import base


class UtilsTests(base.MuranoTestCase):
    def test_validate_quotes(self):
        self.assertEqual(True, utils.validate_quotes('"ab"'))

    def test_validate_quotes_not_closed_quotes(self):
        self.assertRaises(ValueError, utils.validate_quotes, '"ab","b""')

    def test_validate_quotes_no_coma_before_opening_quotes(self):
        self.assertRaises(ValueError, utils.validate_quotes, '"ab""b"')

    def test_split_for_quotes(self):
        self.assertEqual(["a,b", "ac"], utils.split_for_quotes('"a,b","ac"'))

    def test_split_for_quotes_with_backslash(self):
        self.assertEqual(['a"bc', 'de', 'fg,h', r'klm\\', '"nop'],
                         utils.split_for_quotes(r'"a\"bc","de",'
                                                r'"fg,h","klm\\","\"nop"'))
