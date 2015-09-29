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


class IsDifferentTests(base.MuranoTestCase):
    def test_equal_dicts(self):
        obj1 = {'first': 10, 'second': 12}
        obj2 = {'second': 12, 'first': 10}
        comparison = utils.is_different(obj1, obj2)
        self.assertFalse(comparison)

    def test_different_dicts(self):
        obj1 = {'first': 10, 'second': 11}
        obj2 = {'first': 10, 'second': 12}
        comparison = utils.is_different(obj1, obj2)
        self.assertTrue(comparison)

    def test_different_objs(self):
        class Cls1(object):
            a = 10

        class Cls2(object):
            b = 20

        obj1 = Cls1()
        obj2 = Cls2()
        obj3 = Cls1()
        obj3.a = {'one': 14, 'two': [(1, 2, 3), 'more']}

        comparison1 = utils.is_different(obj1, obj2)
        comparison2 = utils.is_different(obj1, obj3)

        self.assertTrue(comparison1)
        self.assertTrue(comparison2)

    def test_equal_objs(self):
        class Cls(object):
            pass

        obj1 = Cls()
        obj2 = Cls()
        obj1.a = {'one': 14, 'two': [(1, 2, 3), 'more']}
        obj2.a = {'one': 14, 'two': [(1, 2, 3), 'more']}

        comparison = utils.is_different(obj1, obj2)

        self.assertFalse(comparison)

    def test_equal_circular_objs(self):
        class Cls(object):
            pass

        lst1 = [1, 2, 3]
        lst2 = [1, 2, 3]
        lst1.append(lst1)
        lst2.append(lst2)

        dct1 = {'one': 10, 'two': lst1}
        dct2 = {'one': 10, 'two': lst1}

        obj1 = Cls()
        obj2 = Cls()
        obj1.a = obj2.a = 10
        obj1.self = obj1
        obj2.self = obj2

        comparison = utils.is_different(lst1, lst2)
        comparison2 = utils.is_different(dct1, dct2)
        comparison3 = utils.is_different(obj1, obj2)

        self.assertFalse(comparison)
        self.assertFalse(comparison2)
        self.assertFalse(comparison3)

    def test_different_circular_objs(self):
        class Cls(object):
            pass

        obj1 = Cls()
        obj2 = Cls()
        obj1.self = obj1
        obj2.self = {'self': obj2}

        dct1 = {'one': [1, 2], 'three': 10}
        dct2 = {'one': [1, 2]}
        dct1['self'] = dct1
        dct2['self'] = dct2

        comparison = utils.is_different(obj1, obj2)
        comparison1 = utils.is_different(dct1, dct2)

        self.assertTrue(comparison)
        self.assertTrue(comparison1)

    def test_strings_are_compared_regardless_of_type(self):
        str1 = 'string'
        str2 = u'string'

        comparison = utils.is_different(str1, str2)

        self.assertFalse(comparison)
