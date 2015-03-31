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
import types

from oslo_utils import encodeutils

import yaql
import yaql.exceptions
import yaql.expressions


class YaqlExpression(object):
    def __init__(self, expression):
        if isinstance(expression, types.StringTypes):
            self._expression = encodeutils.safe_encode(expression)
            self._parsed_expression = yaql.parse(self._expression)
            self._file_position = None
        elif isinstance(expression, YaqlExpression):
            self._expression = expression._expression
            self._parsed_expression = expression._parsed_expression
            self._file_position = expression._file_position
        elif isinstance(expression, yaql.expressions.Expression):
            self._expression = str(expression)
            self._parsed_expression = expression
            self._file_position = None
        else:
            raise TypeError('expression is not of supported types')

    @property
    def expression(self):
        return self._expression

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
    def match(expr):
        if not isinstance(expr, types.StringTypes):
            return False
        if re.match('^[\s\w\d.:]*$', expr):
            return False
        try:
            yaql.parse(expr)
            return True
        except yaql.exceptions.YaqlGrammarException:
            return False
        except yaql.exceptions.YaqlLexicalException:
            return False

    def evaluate(self, context=None):
        return self._parsed_expression.evaluate(context=context)


class YaqlExpressionFilePosition(object):
    def __init__(self, file_path, start_line, start_column, start_index,
                 end_line, end_column, length):
        self._file_path = file_path
        self._start_line = start_line
        self._start_column = start_column
        self._start_index = start_index
        self._end_line = end_line
        self._end_column = end_column
        self._length = length

    @property
    def file_path(self):
        return self._file_path

    @property
    def start_line(self):
        return self._start_line

    @property
    def start_column(self):
        return self._start_column

    @property
    def start_index(self):
        return self._start_index

    @property
    def end_line(self):
        return self._end_line

    @property
    def end_column(self):
        return self._end_column

    @property
    def length(self):
        return self._length
