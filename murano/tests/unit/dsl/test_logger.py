# coding: utf-8
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

import mock

from murano.dsl import helpers
from murano.engine.system import logger
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestLogger(test_case.DslTestCase):

    FORMAT_CALLS = [
        mock.call(mock.ANY, 'str', (), {}),
        mock.call(mock.ANY, u'тест', (), {}),
        mock.call(mock.ANY, 'str', (1,), {}),
        mock.call(mock.ANY, 'str {0}', ('message',), {}),
        mock.call(mock.ANY, 'str {message}', (), {'message': 'message'}),
        mock.call(mock.ANY, 'str {message}{0}', (), {})]

    LOG_CALLS = FORMAT_CALLS

    def setUp(self):
        super(TestLogger, self).setUp()
        self._runner = self.new_runner(om.Object('TestLogger'))
        self.package_loader.load_package('io.murano', None).register_class(
            logger.Logger)

    def test_create(self):
        logger_instance = self._runner.testCreate()
        self.assertTrue(
            helpers.is_instance_of(logger_instance, 'io.murano.system.Logger'),
            'Function should return io.murano.system.Logger instance')

    def _create_logger_mock(self):
        logger_instance = self._runner.testCreate()
        logger_ext = logger_instance.extension

        underlying_logger_mock = mock.MagicMock()
        logger_ext._underlying_logger = underlying_logger_mock
        logger_ext._underlying_logger.return_value = None

        format_mock = mock.MagicMock(return_value='format_mock')
        # do not verify number of conversions to string
        format_mock.__str__ = mock.MagicMock(return_value='format_mock')
        format_mock.__unicode__ = mock.MagicMock(return_value='format_mock')

        logger_ext._format_without_exceptions = format_mock

        return logger_instance, format_mock, underlying_logger_mock

    def test_trace(self):
        logger_instance, format_mock, underlying_logger_mock \
            = self._create_logger_mock()
        log_method = mock.MagicMock()

        underlying_logger_mock.trace = log_method
        self._runner.testTrace(logger_instance)

        format_mock.assert_has_calls(self.FORMAT_CALLS, any_order=False)
        self.assertEqual(log_method.call_count, len(self.LOG_CALLS))

    def test_debug(self):
        logger_instance, format_mock, underlying_logger_mock \
            = self._create_logger_mock()
        log_method = mock.MagicMock()

        underlying_logger_mock.debug = log_method
        self._runner.testDebug(logger_instance)

        format_mock.assert_has_calls(self.FORMAT_CALLS, any_order=False)
        self.assertEqual(log_method.call_count, len(self.LOG_CALLS))

    def test_info(self):
        logger_instance, format_mock, underlying_logger_mock \
            = self._create_logger_mock()
        log_method = mock.MagicMock()

        underlying_logger_mock.info = log_method
        self._runner.testInfo(logger_instance)

        format_mock.assert_has_calls(self.FORMAT_CALLS, any_order=False)
        self.assertEqual(log_method.call_count, len(self.LOG_CALLS))

    def test_warning(self):
        logger_instance, format_mock, underlying_logger_mock \
            = self._create_logger_mock()
        log_method = mock.MagicMock()

        underlying_logger_mock.warning = log_method
        self._runner.testWarning(logger_instance)

        format_mock.assert_has_calls(self.FORMAT_CALLS, any_order=False)
        self.assertEqual(log_method.call_count, len(self.LOG_CALLS))

    def test_error(self):
        logger_instance, format_mock, underlying_logger_mock \
            = self._create_logger_mock()
        log_method = mock.MagicMock()

        underlying_logger_mock.error = log_method
        self._runner.testError(logger_instance)

        format_mock.assert_has_calls(self.FORMAT_CALLS, any_order=False)
        self.assertEqual(log_method.call_count, len(self.FORMAT_CALLS))

    def test_critical(self):
        logger_instance, format_mock, underlying_logger_mock \
            = self._create_logger_mock()
        log_method = mock.MagicMock()

        underlying_logger_mock.critical = log_method
        self._runner.testCritical(logger_instance)

        format_mock.assert_has_calls(self.FORMAT_CALLS, any_order=False)
        self.assertEqual(log_method.call_count, len(self.LOG_CALLS))

    def test_exception(self):
        logger_instance, format_mock, underlying_logger_mock = \
            self._create_logger_mock()
        log_method = mock.MagicMock()

        underlying_logger_mock.error = log_method
        self._runner.testException(logger_instance)

        format_mock.assert_has_calls(self.FORMAT_CALLS, any_order=False)
        self.assertEqual(log_method.call_count, len(self.LOG_CALLS))
