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


import six

from murano.dsl import constants
from murano.dsl import dsl_exception
from murano.dsl import exceptions
from murano.dsl import expressions
from murano.dsl import helpers
from murano.dsl import yaql_expression


class CodeBlock(expressions.DslExpression):
    def __init__(self, body):
        body = helpers.list_value(body)
        self.code_block = list(map(expressions.parse_expression, body))

    def execute(self, context):
        for expr in self.code_block:
            if hasattr(expr, 'virtual_instruction'):
                instruction = expr.virtual_instruction
                context[constants.CTX_CURRENT_INSTRUCTION] = instruction

            try:
                expr.execute(context)
            except (dsl_exception.MuranoPlException,
                    exceptions.InternalFlowException):
                raise
            except Exception as ex:
                raise dsl_exception.MuranoPlException.from_python_exception(
                    ex, context)


class MethodBlock(CodeBlock):
    def __init__(self, body, name=None):
        super(MethodBlock, self).__init__(body)
        self._name = name

    def execute(self, context):
        new_context = context.create_child_context()
        new_context[constants.CTX_VARIABLE_SCOPE] = True
        try:
            super(MethodBlock, self).execute(new_context)
        except exceptions.ReturnException as e:
            return e.value
        except exceptions.BreakException:
            raise exceptions.DslInvalidOperationError(
                'Break cannot be used on method level')
        except exceptions.ContinueException:
            raise exceptions.DslInvalidOperationError(
                'Continue cannot be used on method level')
        else:
            return None


class ReturnMacro(expressions.DslExpression):
    def __init__(self, Return):
        self._value = Return

    def execute(self, context):
        raise exceptions.ReturnException(
            helpers.evaluate(self._value, context))


class BreakMacro(expressions.DslExpression):
    def __init__(self, Break):
        if Break:
            raise exceptions.DslSyntaxError('Break cannot have value')

    def execute(self, context):
        raise exceptions.BreakException()


class ContinueMacro(expressions.DslExpression):
    def __init__(self, Continue):
        if Continue:
            raise exceptions.DslSyntaxError('Continue cannot have value')

    def execute(self, context):
        raise exceptions.ContinueException()


class ParallelMacro(CodeBlock):
    def __init__(self, Parallel, Limit=None):
        super(ParallelMacro, self).__init__(Parallel)
        self._limit = Limit or len(self.code_block)

    def execute(self, context):
        if not self.code_block:
            return
        limit = helpers.evaluate(self._limit, context)
        helpers.parallel_select(
            self.code_block,
            lambda expr: expr.execute(context.create_child_context()),
            limit)


class IfMacro(expressions.DslExpression):
    def __init__(self, If, Then, Else=None):
        self._code1 = CodeBlock(Then)
        self._code2 = None if Else is None else CodeBlock(Else)
        self._condition = If

    def execute(self, context):
        if helpers.evaluate(self._condition, context):
            self._code1.execute(context)
        elif self._code2 is not None:
            self._code2.execute(context)


class WhileDoMacro(expressions.DslExpression):
    def __init__(self, While, Do):
        if not isinstance(While, yaql_expression.YaqlExpression):
            raise TypeError()
        self._code = CodeBlock(Do)
        self._condition = While

    def execute(self, context):
        while self._condition(context):
            try:
                self._code.execute(context)
            except exceptions.BreakException:
                break
            except exceptions.ContinueException:
                continue


class ForMacro(expressions.DslExpression):
    def __init__(self, For, In, Do):
        if not isinstance(For, six.string_types):
            raise exceptions.DslSyntaxError(
                'For value must be of string type')
        self._code = CodeBlock(Do)
        self._var = For
        self._collection = In

    def execute(self, context):
        collection = helpers.evaluate(self._collection, context)
        for t in collection:
            context[self._var] = t
            try:
                self._code.execute(context)
            except exceptions.BreakException:
                break
            except exceptions.ContinueException:
                continue


class RepeatMacro(expressions.DslExpression):
    def __init__(self, Repeat, Do):
        if not isinstance(Repeat, (int, yaql_expression.YaqlExpression)):
            raise exceptions.DslSyntaxError(
                'Repeat value must be either int or expression')
        self._count = Repeat
        self._code = CodeBlock(Do)

    def execute(self, context):
        count = helpers.evaluate(self._count, context)
        for _ in range(0, count):
            try:
                self._code.execute(context)
            except exceptions.BreakException:
                break
            except exceptions.ContinueException:
                continue


class MatchMacro(expressions.DslExpression):
    def __init__(self, Match, Value, Default=None):
        if not isinstance(Match, dict):
            raise exceptions.DslSyntaxError(
                'Match value must be of dictionary type')
        self._switch = Match
        self._value = Value
        self._default = None if Default is None else CodeBlock(Default)

    def execute(self, context):
        match_value = helpers.evaluate(self._value, context)
        for key, value in self._switch.items():
            if key == match_value:
                CodeBlock(value).execute(context)
                return
        if self._default is not None:
            self._default.execute(context)


class SwitchMacro(expressions.DslExpression):
    def __init__(self, Switch, Default=None):
        if not isinstance(Switch, dict):
            raise exceptions.DslSyntaxError(
                'Switch value must be of dictionary type')
        self._switch = Switch
        self._default = None if Default is None else CodeBlock(Default)

    def execute(self, context):
        matched = False
        for key, value in self._switch.items():
            if helpers.evaluate(key, context):
                matched = True
                CodeBlock(value).execute(context)

        if self._default is not None and not matched:
            self._default.execute(context)


class DoMacro(expressions.DslExpression):
    def __init__(self, Do):
        self._code = CodeBlock(Do)

    def execute(self, context):
        self._code.execute(context)


def register():
    expressions.register_macro(DoMacro)
    expressions.register_macro(ReturnMacro)
    expressions.register_macro(BreakMacro)
    expressions.register_macro(ContinueMacro)
    expressions.register_macro(ParallelMacro)
    expressions.register_macro(IfMacro)
    expressions.register_macro(WhileDoMacro)
    expressions.register_macro(ForMacro)
    expressions.register_macro(RepeatMacro)
    expressions.register_macro(MatchMacro)
    expressions.register_macro(SwitchMacro)
