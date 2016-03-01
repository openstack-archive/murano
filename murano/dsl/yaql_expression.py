#    Copyright (c) 2014 Mirantis, Inc.
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

import re

import six
from yaql.language import exceptions as yaql_exceptions
from yaql.language import expressions

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import yaql_integration


EXPRESSION_REGEX = re.compile('^[\s\w\d.]*$')


class YaqlExpression(dsl_types.YaqlExpression):
    def __init__(self, expression, version):
        self._version = version
        if isinstance(expression, six.string_types):
            self._expression = six.text_type(expression)
            self._parsed_expression = yaql_integration.parse(
                self._expression, version)
            self._file_position = None
        elif isinstance(expression, YaqlExpression):
            self._expression = expression._expression
            self._parsed_expression = expression._parsed_expression
            self._file_position = expression._file_position
        elif isinstance(expression, expressions.Statement):
            self._expression = six.text_type(expression)
            self._parsed_expression = expression
            self._file_position = None
        else:
            raise TypeError('expression is not of supported types')

    @property
    def expression(self):
        return self._expression

    @property
    def version(self):
        return self._version

    @property
    def source_file_position(self):
        return self._file_position

    @source_file_position.setter
    def source_file_position(self, value):
        self._file_position = value

    def __repr__(self):
        return 'YAQL(%s)' % self._expression

    def __str__(self):
        return self._expression

    @staticmethod
    def is_expression(expression, version):
        if not isinstance(expression, six.string_types):
            return False
        if EXPRESSION_REGEX.match(expression):
            return False
        try:
            yaql_integration.parse(expression, version)
            return True
        except yaql_exceptions.YaqlParsingException:
            return False

    def __call__(self, context):
        if context:
            context[constants.CTX_CURRENT_INSTRUCTION] = self
        return self._parsed_expression.evaluate(context=context)
