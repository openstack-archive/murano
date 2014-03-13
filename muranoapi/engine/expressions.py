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

import types

from muranoapi.engine import helpers
from muranoapi.engine import lhs_expression as lhs
from muranoapi.engine import yaql_expression


_macros = []


def register_macro(cls):
    _macros.append(cls)


class DslExpression(object):
    def execute(self, context, murano_class):
        pass


class Statement(DslExpression):
    def __init__(self, statement):
        if isinstance(statement, yaql_expression.YaqlExpression):
            key = None
            value = statement
        elif isinstance(statement, types.DictionaryType):
            if len(statement) != 1:
                raise SyntaxError()
            key = statement.keys()[0]
            value = statement[key]
        else:
            raise SyntaxError()

        self._destination = None if not key else lhs.LhsExpression(key)
        self._expression = value

    @property
    def destination(self):
        return self._destination

    @property
    def expression(self):
        return self._expression

    def execute(self, context, murano_class):
        result = helpers.evaluate(self.expression, context)
        if self.destination:
            self.destination(result, context, murano_class)

        return result


def parse_expression(expr):
    result = None
    if isinstance(expr, yaql_expression.YaqlExpression):
        result = Statement(expr)
    elif isinstance(expr, types.DictionaryType):
        kwds = {}
        for key, value in expr.iteritems():
            if isinstance(key, yaql_expression.YaqlExpression):
                if result is not None:
                    raise ValueError()
                result = Statement(expr)
            else:
                kwds[key] = value

        if result is None:
            for cls in _macros:
                try:
                    return cls(**kwds)
                except TypeError:
                    continue

    if result is None:
        raise SyntaxError()
    return result
