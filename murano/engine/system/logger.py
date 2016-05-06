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

from oslo_log import log as logging
from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import dsl

NAME_TEMPLATE = u'applications.{0}'

inject_format = specs.inject(
    '_Logger__yaql_format_function',
    yaqltypes.Delegate('format'))


@dsl.name('io.murano.system.Logger')
class Logger(object):
    """Logger object for MuranoPL.

    Instance of this object returned by 'logger' YAQL function
    and should not be instantiated directly
    """

    def __init__(self, logger_name):
        self._underlying_logger = logging.getLogger(
            NAME_TEMPLATE.format(logger_name))

    @specs.parameter('_Logger__message', yaqltypes.String())
    @inject_format
    def trace(__self, __yaql_format_function, __message, *args, **kwargs):
        __self._log(__self._underlying_logger.trace,
                    __yaql_format_function, __message, args, kwargs)

    @specs.parameter('_Logger__message', yaqltypes.String())
    @inject_format
    def debug(__self, __yaql_format_function, __message, *args, **kwargs):
        __self._log(__self._underlying_logger.debug,
                    __yaql_format_function, __message, args, kwargs)

    @specs.parameter('_Logger__message', yaqltypes.String())
    @inject_format
    def info(__self, __yaql_format_function, __message, *args, **kwargs):
        __self._log(__self._underlying_logger.info,
                    __yaql_format_function, __message, args, kwargs)

    @specs.parameter('_Logger__message', yaqltypes.String())
    @inject_format
    def warning(__self, __yaql_format_function, __message, *args, **kwargs):
        __self._log(__self._underlying_logger.warning,
                    __yaql_format_function, __message, args, kwargs)

    @specs.parameter('_Logger__message', yaqltypes.String())
    @inject_format
    def error(__self, __yaql_format_function, __message, *args, **kwargs):
        __self._log(__self._underlying_logger.error,
                    __yaql_format_function, __message, args, kwargs)

    @specs.parameter('_Logger__message', yaqltypes.String())
    @inject_format
    def critical(__self, __yaql_format_function,
                 __message, *args, **kwargs):
        __self._log(__self._underlying_logger.critical,
                    __yaql_format_function, __message, args, kwargs)

    @specs.parameter('_Logger__message', yaqltypes.String())
    @inject_format
    def exception(__self, __yaql_format_function,
                  __exc, __message, *args, **kwargs):
        """Print error message and stacktrace"""
        stack_trace_message = u'\n'.join([
            __self._format_without_exceptions(
                __yaql_format_function, __message, args, kwargs),
            __exc['stackTrace']().toString()
        ])
        __self._underlying_logger.error(stack_trace_message)

    def _format_without_exceptions(self, format_function,
                                   message, args, kwargs):
        """Wrap YAQL function "format" to suppress exceptions

        Wrap YAQL function "format" to suppress exceptions
        that may be raised when message cannot be formatted
        due to invalid parameters provided
        We do not want to break program workflow
        even when formatting parameters are incorrect
        """
        try:
            message = format_function(message, *args, **kwargs)
        except (IndexError, KeyError):
            # NOTE(akhivin): we do not want break program workflow
            # even formatting parameters are incorrect
            self._underlying_logger.warning(
                u'Can not format string: {0}'.format(message))
        return message

    def _log(self, log_function, yaql_format_function, message, args, kwargs):
        log_function(
            self._format_without_exceptions(
                yaql_format_function, message, args, kwargs))
