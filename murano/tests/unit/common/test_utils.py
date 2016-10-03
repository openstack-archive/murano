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

import datetime
import json

from murano.common import utils

from murano.tests.unit import base


class UtilsTests(base.MuranoTestCase):

    def test_validate_quotes(self):
        self.assertTrue(utils.validate_quotes('"ab"'))

    def test_validate_quotes_not_closed_quotes(self):
        self.assertRaises(ValueError, utils.validate_quotes, '"ab","b""')

    def test_validate_quotes_not_opened_quotes(self):
        self.assertRaises(ValueError, utils.validate_quotes, '""ab","b"')

    def test_validate_quotes_no_coma_before_opening_quotes(self):
        self.assertRaises(ValueError, utils.validate_quotes, '"ab""b"')

    def test_split_for_quotes(self):
        self.assertEqual(["a,b", "ac"], utils.split_for_quotes('"a,b","ac"'))

    def test_split_for_quotes_with_backslash(self):
        self.assertEqual(['a"bc', 'de', 'fg,h', r'klm\\', '"nop'],
                         utils.split_for_quotes(r'"a\"bc","de",'
                                                r'"fg,h","klm\\","\"nop"'))

    def test_validate_body(self):
        json_schema = json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
        self.assertIsNotNone(utils.validate_body(json_schema))

        json_schema = json.dumps(['body', {'body': ('baz', None, 1.0, 2)}])
        self.assertIsNotNone(utils.validate_body(json_schema))

    def test_build_entity_map(self):
        entity = {"?": {"fun": "id"}}
        self.assertEqual({}, utils.build_entity_map(entity))

        entity = {"?": {"id": "id"}}
        self.assertEqual({'id': {'?': {'id': 'id'}}},
                         utils.build_entity_map(entity))

        entity = [{"?": {"id": "id1"}}, {"?": {"id": "id2"}}]
        self.assertEqual({'id1': {'?': {'id': 'id1'}},
                          'id2': {'?': {'id': 'id2'}}},
                         utils.build_entity_map(entity))

    def test_is_different(self):
        t1 = "Hello"
        t2 = "World"
        self.assertTrue(utils.is_different(t1, t2))

        t1 = "Hello"
        t2 = "Hello"
        self.assertFalse(utils.is_different(t1, t2))

        t1 = {1, 2, 3, 4}
        t2 = t1
        self.assertFalse(utils.is_different(t1, t2))

        t2 = {1, 2, 3}
        self.assertTrue(utils.is_different(t1, t2))

        t1 = [1, 2, {1, 2, 3, 4}]
        t1[0] = t1
        self.assertTrue(utils.is_different(t1, t2))

        t1 = [t2]
        t2 = [t1]
        self.assertTrue(utils.is_different(t1, t2))

        t1 = [{1, 2, 3}, {1, 2, 3}]
        t2 = [{1, 2, 3}, {1, 2}]
        self.assertTrue(utils.is_different(t1, t2))

        t1 = datetime.date(2016, 8, 8)
        t2 = datetime.date(2016, 8, 7)
        self.assertTrue(utils.is_different(t1, t2))

        t1 = {1: 1, 2: 2, 3: 3}
        t2 = {1: 1, 2: 4, 3: 3}
        self.assertTrue(utils.is_different(t1, t2))

        t1 = {1: 1, 2: 2, 3: 3, 4: {"a": "hello", "b": [1, 2, 3]}}
        t2 = {1: 1, 2: 2, 3: 3, 4: {"a": "hello", "b": "world\n\n\nEnd"}}
        self.assertTrue(utils.is_different(t1, t2))

        t1 = {1: 1, 2: 2, 3: 3, 4: {"a": "hello", "b": [1, 2, 5]}}
        t2 = {1: 1, 2: 2, 3: 3, 4: {"a": "hello", "b": [1, 3, 2, 5]}}
        self.assertTrue(utils.is_different(t1, t2))

        class ClassA(object):
            __slots__ = ['x', 'y']

            def __init__(self, x, y):
                self.x = x
                self.y = y

        t1 = ClassA(1, 1)
        t2 = ClassA(1, 2)
        self.assertTrue(utils.is_different(t1, t2))

        t1 = [1, 2, 3]
        t1.append(t1)

        t2 = [1, 2, 4]
        t2.append(t2)
        self.assertTrue(utils.is_different(t1, t2))

        t1 = [1, 2, 3]
        t2 = [1, 2, 4]
        t2.append(t1)
        t1.append(t2)
        self.assertTrue(utils.is_different(t1, t2))

        t1 = utils
        t2 = datetime
        self.assertTrue(utils.is_different(t1, t2))

        t2 = "Not a module"
        self.assertTrue(utils.is_different(t1, t2))
