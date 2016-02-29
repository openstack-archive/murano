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

import inspect
import os.path
import re

from testtools import matchers

from murano.dsl import dsl_exception
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestExceptions(test_case.DslTestCase):
    def setUp(self):
        super(TestExceptions, self).setUp()

        def exception_func():
            exc = LookupError('just random Python exception')
            frameinfo = inspect.getframeinfo(inspect.currentframe())
            exc._position = \
                os.path.basename(frameinfo.filename), frameinfo.lineno + 4
            # line below must be exactly 4 lines after currentframe()
            raise exc

        self.register_function(exception_func, 'raisePythonException')
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

    def test_stack_trace(self):
        self._runner.preserve_exception = True
        e = self.assertRaises(
            dsl_exception.MuranoPlException,
            self._runner.testStackTrace)
        call_stack = e.format()
        self.assertThat(
            call_stack,
            matchers.StartsWith(
                'LookupError: just random Python exception'))

        self.assertIsInstance(e.original_exception, LookupError)

        filename, line = e.original_exception._position
        self.assertThat(
            call_stack,
            matchers.MatchesRegex(
                r'.*^  File \".*ExceptionHandling\.yaml\", '
                r'line \d+:\d+ in method testStackTrace .*'
                r'of type ExceptionHandling$.*'
                r'^  File \".*{0}\", line {1} '
                r'in method exception_func$.*'.format(filename, line),
                re.MULTILINE | re.DOTALL))
