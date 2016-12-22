# Copyright (c) 2015 Mirantis, Inc.
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
import warnings

from murano.dsl import exceptions
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestFindClass(test_case.DslTestCase):

    def setUp(self):
        super(TestFindClass, self).setUp()
        self._runner = self.new_runner(om.Object('TestFindClass'))

    def test_find_class_with_prefix(self):
        with warnings.catch_warnings(record=True) as capture:
            self.assertIsNone(self._runner.testFindClassWithPrefix())
        self.assertEqual(DeprecationWarning, capture[-1].category)
        observed = capture[-1].message
        expected = ("Plugin io.murano.extensions.io.murano.test.TestFixture "
                    "was not found, but a io.murano.test.TestFixture was "
                    "found instead and will be used. This could be caused by "
                    "recent change in plugin naming scheme. If you are "
                    "developing applications targeting this plugin consider "
                    "changing its name")
        self.assertEqual(expected, six.text_type(observed))

    def test_find_class_short_name(self):
        self.assertIsNone(self._runner.testFindClassShortName())

    def test_class_with_prefix_not_found(self):
        observed = self.assertRaises(exceptions.NoClassFound,
                                     self._runner.testClassWithPrefixNotFound)
        expected = ('Class "io.murano.extensions.io.murano.test.TestFixture1" '
                    'is not found in io.murano/0.0.0, tests/0.0.0')
        self.assertEqual(expected, six.text_type(observed))
