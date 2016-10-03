#    Copyright (c) 2016 AT&T
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

import mock
import testtools

from murano.dsl import murano_method
from murano.dsl import murano_type
from murano.dsl import object_store
from murano.engine.system import test_fixture
from murano.tests.unit import base


class TestTestFixture(base.MuranoTestCase):
    def setUp(self):
        super(TestTestFixture, self).setUp()

        self.mock_class = mock.MagicMock(spec=murano_type.MuranoClass)
        self.mock_method = mock.MagicMock(spec=murano_method.MuranoMethod)
        self.mock_object_store = mock.Mock(spec=object_store.ObjectStore)

        self.test_fixture = test_fixture.TestFixture()

        self.addCleanup(mock.patch.stopall)

    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_finish_env(self, execution_session):
        self.assertIsNone(self.test_fixture.finish_env())
        self.assertTrue(execution_session.called)

    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_start_env(self, execution_session):
        self.assertIsNone(self.test_fixture.start_env())
        self.assertTrue(execution_session.called)

    @mock.patch("murano.dsl.helpers.get_executor")
    def test_load(self, executor):
        executor.return_value = self.mock_object_store
        model = "test"
        tf_load = self.test_fixture.load(model)
        self.assertEqual(self.test_fixture.load(model), tf_load)

    def test_assert_true(self):
        expr = (7 > 3)
        message = None
        # Calls assertTrue in super class
        self.test_fixture.assert_true(expr, message)

    def test_assert_false(self):
        expr = (3 != 3)
        message = None
        # Calls assertFalse in super class
        self.test_fixture.assert_false(expr, message)

    def test_assert_in(self):
        needle = 7
        haystack = [3, 7, 8, 9, 22]
        message = None
        # Calls assertIn in super class
        self.test_fixture.assert_in(needle, haystack, message)

    def test_assert_not_in(self):
        needle = 16
        haystack = [3, 7, 8, 9, 22]
        message = None
        # Calls assertNotIn in super class
        self.test_fixture.assert_not_in(needle, haystack, message)

    def test_assert_true_fails(self):
        expr = (7 < 3)
        message = None
        self.assertRaises(AssertionError,
                          self.test_fixture.assert_true, expr, message)

    def test_assert_false_fails(self):
        expr = (3 == 3)
        message = None
        self.assertRaises(AssertionError,
                          self.test_fixture.assert_false, expr, message)

    def test_assert_in_fails(self):
        needle = 25
        haystack = [3, 7, 8, 9, 22]
        message = None
        self.assertRaises(testtools.matchers._impl.MismatchError,
                          self.test_fixture.assert_in, needle,
                          haystack, message)

    def test_assert_not_in_fails(self):
        needle = 22
        haystack = [3, 7, 8, 9, 22]
        message = None
        self.assertRaises(testtools.matchers._impl.MismatchError,
                          self.test_fixture.assert_not_in, needle,
                          haystack, message)
