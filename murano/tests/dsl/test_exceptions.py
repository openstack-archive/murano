# Copyright (c) 2014 Mirantis, Inc.
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

from murano.dsl import dsl_exception
from murano.tests.dsl.foundation import object_model as om
from murano.tests.dsl.foundation import test_case


class TestExceptions(test_case.DslTestCase):
    def setUp(self):
        super(TestExceptions, self).setUp()
        self._runner = self.new_runner(om.Object('ExceptionHandling'))

    def test_throw_catch(self):
        self._runner.testThrow(1)
        self.assertEqual(
            ['enter try', u'exception message', 'finally section'],
            self.traces)

    def test_rethrow(self):
        e = self.assertRaises(
            dsl_exception.MuranoPlException,
            self._runner.testThrow, 2)

        self.assertEqual(['anotherExceptionName'], e.names)
        self.assertEqual('exception message 2', e.message)
        self.assertEqual('[anotherExceptionName]: exception message 2', str(e))

        self.assertEqual(
            ['enter try', 'exception message 2',
             'rethrow', 'finally section'],
            self.traces)

    def test_catch_all_catch(self):
        self._runner.testThrow(3)
        self.assertEqual(
            ['enter try', 'catch all',
             'exception message 3', 'finally section'],
            self.traces)

    def test_no_throw(self):
        self._runner.testThrow(4)
        self.assertEqual(
            ['enter try', 'exit try', 'else section', 'finally section'],
            self.traces)
