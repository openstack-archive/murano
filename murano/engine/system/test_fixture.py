# Copyright (c) 2015 Mirantis Inc.
#
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

import testtools

from murano.dsl import dsl
from murano.dsl import helpers


@dsl.name('io.murano.test.TestFixture')
class TestFixture(object):
    def __init__(self):
        self._test_case = testtools.TestCase('__init__')

    def load(self, model):
        exc = helpers.get_executor()
        return exc.load(model)

    def finish_env(self):
        session = helpers.get_execution_session()
        session.finish()

    def start_env(self):
        session = helpers.get_execution_session()
        session.start()

    def assert_equal(self, expected, observed, message=None):
        self._test_case.assertEqual(expected, observed, message)

    def assert_true(self, expr, message=None):
        self._test_case.assertTrue(expr, message)

    def assert_false(self, expr, message=None):
        self._test_case.assertFalse(expr, message)

    def assert_in(self, needle, haystack, message=None):
        self._test_case.assertIn(needle, haystack, message)

    def assert_not_in(self, needle, haystack, message=None):
        self._test_case.assertNotIn(needle, haystack, message)
