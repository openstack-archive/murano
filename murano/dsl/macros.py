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

import eventlet.greenpool as greenpool
import yaql.context

import murano.dsl.dsl_exception as dsl_exception
import murano.dsl.exceptions as exceptions
import murano.dsl.expressions as expressions
import murano.dsl.helpers as helpers
import murano.dsl.yaql_expression as yaql_expression


class CodeBlock(expressions.DslExpression):
    def __init__(self, body, breakable=False):
        if not isinstance(body, types.ListType):
            body = [body]
        self.code_block = map(expressions.parse_expression, body)
        self._breakable = breakable

    def execute(self, context, murano_class):
        try:
            for expr in self.code_block:
                def action():
                    try:
                        expr.execute(context, murano_class)
                    except dsl_exception.MuranoPlException:
                        raise
                    except Exception as ex:
                        raise dsl_exception.MuranoPlException.\
                            from_python_exception(ex, context)

                if hasattr(expr, 'virtual_instruction'):
                    instruction = expr.virtual_instruction
                    helpers.execute_instruction(instruction, action, context)
                else:
                    action()
        except exceptions.BreakException as e:
            if self._breakable:
                raise e
            else:
                raise SyntaxError()


class MethodBlock(CodeBlock):
    def __init__(self, body, name=None):
        super(MethodBlock, self).__init__(body)
        self._name = name

    def execute(self, context, murano_class):
        new_context = yaql.context.Context(context)
        new_context.set_data(self._name, '?currentMethod')
        try:
            super(MethodBlock, self).execute(new_context, murano_class)
        except exceptions.ReturnException as e:
            return e.value
        else:
            return None


class ReturnMacro(expressions.DslExpression):
    def __init__(self, Return):
        self._value = Return

    def execute(self, context, murano_class):
        raise exceptions.ReturnException(
            helpers.evaluate(self._value, context))


class BreakMacro(expressions.DslExpression):
    def __init__(self, Break):
        if Break:
            raise SyntaxError()

    def execute(self, context, murano_class):
        raise exceptions.BreakException()


class ParallelMacro(CodeBlock):
    def __init__(self, Parallel, Limit=None):
        super(ParallelMacro, self).__init__(Parallel)
        if Limit:
            self._limit = yaql_expression.YaqlExpression(Limit)
        else:
            self._limit = len(self.code_block)

    def execute(self, context, murano_class):
        if not self.code_block:
            return
        gpool = greenpool.GreenPool(helpers.evaluate(self._limit, context))
        for expr in self.code_block:
            gpool.spawn_n(expr.execute, context, murano_class)
        gpool.waitall()


class IfMacro(expressions.DslExpression):
    def __init__(self, If, Then, Else=None):
        if not isinstance(If, yaql_expression.YaqlExpression):
            raise TypeError()
        self._code1 = CodeBlock(Then)
        self._code2 = None if Else is None else CodeBlock(Else)
        self._condition = If

    def execute(self, context, murano_class):
        res = self._condition.evaluate(context)
        if not isinstance(res, types.BooleanType):
            raise TypeError()
        if res:
            self._code1.execute(context, murano_class)
        elif self._code2 is not None:
            self._code2.execute(context, murano_class)


class WhileDoMacro(expressions.DslExpression):
    def __init__(self, While, Do):
        if not isinstance(While, yaql_expression.YaqlExpression):
            raise TypeError()
        self._code = CodeBlock(Do, breakable=True)
        self._condition = While

    def execute(self, context, murano_class):
        while True:
            res = self._condition.evaluate(context)
            if not isinstance(res, types.BooleanType):
                raise TypeError()
            try:
                if res:
                    self._code.execute(context, murano_class)
                else:
                    break
            except exceptions.BreakException:
                break


class ForMacro(expressions.DslExpression):
    def __init__(self, For, In, Do):
        if not isinstance(For, types.StringTypes):
            raise TypeError()
        self._code = CodeBlock(Do, breakable=True)
        self._var = For
        self._collection = In

    def execute(self, context, murano_class):
        collection = helpers.evaluate(self._collection, context)
        child_context = yaql.context.Context(context)
        for t in collection:
            child_context.set_data(t, self._var)
            try:
                self._code.execute(child_context, murano_class)
            except exceptions.BreakException:
                break


class RepeatMacro(expressions.DslExpression):
    def __init__(self, Repeat, Do):
        if not isinstance(Repeat, (int, yaql_expression.YaqlExpression)):
            raise SyntaxError()
        self._count = Repeat
        self._code = CodeBlock(Do, breakable=True)

    def execute(self, context, murano_class):
        count = helpers.evaluate(self._count, context)
        for t in range(0, count):
            try:
                self._code.execute(context, murano_class)
            except exceptions.BreakException:
                break


class MatchMacro(expressions.DslExpression):
    def __init__(self, Match, Value, Default=None):
        if not isinstance(Match, types.DictionaryType):
            raise SyntaxError()
        self._switch = Match
        self._value = Value
        self._default = None if Default is None else CodeBlock(Default)

    def execute(self, context, murano_class):
        match_value = helpers.evaluate(self._value, context)
        for key, value in self._switch.iteritems():
            if key == match_value:
                CodeBlock(value).execute(context, murano_class)
                return
        if self._default is not None:
            self._default.execute(context, murano_class)


class SwitchMacro(expressions.DslExpression):
    def __init__(self, Switch, Default=None):
        if not isinstance(Switch, types.DictionaryType):
            raise SyntaxError()
        self._switch = Switch
        self._default = None if Default is None else CodeBlock(Default)

    def execute(self, context, murano_class):
        matched = False
        for key, value in self._switch.iteritems():
            if not isinstance(key, (yaql_expression.YaqlExpression,
                                    types.BooleanType)):
                raise SyntaxError()
            res = helpers.evaluate(key, context)
            if not isinstance(res, types.BooleanType):
                raise TypeError()
            if res:
                matched = True
                child_context = yaql.context.Context(context)
                CodeBlock(value).execute(child_context, murano_class)

        if self._default is not None and not matched:
            self._default.execute(context, murano_class)


class DoMacro(expressions.DslExpression):
    def __init__(self, Do):
        self._code = CodeBlock(Do)

    def execute(self, context, murano_class):
        child_context = yaql.context.Context(context)
        self._code.execute(child_context, murano_class)


def register():
    expressions.register_macro(DoMacro)
    expressions.register_macro(ReturnMacro)
    expressions.register_macro(BreakMacro)
    expressions.register_macro(ParallelMacro)
    expressions.register_macro(IfMacro)
    expressions.register_macro(WhileDoMacro)
    expressions.register_macro(ForMacro)
    expressions.register_macro(RepeatMacro)
    expressions.register_macro(MatchMacro)
    expressions.register_macro(SwitchMacro)
