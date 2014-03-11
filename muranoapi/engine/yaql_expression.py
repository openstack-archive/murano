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

import yaql
import yaql.exceptions


class YaqlExpression(object):
    def __init__(self, expression):
        self._expression = str(expression)
        self._parsed_expression = yaql.parse(self._expression)

    def expression(self):
        return self._expression

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
