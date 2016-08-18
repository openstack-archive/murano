#    Copyright (c) 2016 Mirantis, Inc.
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

from yaql.language import exceptions as yaql_exceptions
from yaql.language import expressions
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import contracts
from murano.dsl import exceptions
from murano.dsl import helpers


class Check(contracts.ContractMethod):
    name = 'check'

    @specs.parameter('predicate', yaqltypes.YaqlExpression())
    @specs.parameter('msg', yaqltypes.String(nullable=True))
    def __init__(self, engine, predicate, msg=None):
        self.engine = engine
        self.predicate = predicate
        self.msg = msg

    def _call_predicate(self, value):
        context = self.root_context.create_child_context()
        context['$'] = value
        return self.predicate(utils.NO_VALUE, context, self.engine)

    def validate(self):
        if isinstance(self.value, contracts.ObjRef) or self._call_predicate(
                self.value):
            return self.value
        else:
            msg = self.msg
            if not msg:
                msg = "Value {0} doesn't match predicate".format(
                    helpers.format_scalar(self.value))
            raise exceptions.ContractViolationException(msg)

    def transform(self):
        return self.validate()

    def generate_schema(self):
        rest = [True]
        while rest:
            if (isinstance(self.predicate, expressions.BinaryOperator) and
                    self.predicate.operator == 'and'):
                rest = self.predicate.args[1]
                self.predicate = self.predicate.args[0]
            else:
                rest = []
            res = extract_pattern(self.predicate, self.engine,
                                  self.root_context)
            if res is not None:
                self.value.update(res)
            self.predicate = rest
        return self.value


def is_dollar(expr):
    """Check $-expressions in YAQL AST"""
    return (isinstance(expr, expressions.GetContextValue) and
            expr.path.value in ('$', '$1'))


def extract_pattern(expr, engine, context):
    """Translation of certain known patterns of check() contract expressions"""
    if isinstance(expr, expressions.BinaryOperator):
        ops = ('>', '<', '>=', '<=')
        if expr.operator in ops:
            op_index = ops.index(expr.operator)
            if is_dollar(expr.args[0]):
                constant = evaluate_constant(expr.args[1], engine, context)
                if constant is None:
                    return None
            elif is_dollar(expr.args[1]):
                constant = evaluate_constant(expr.args[0], engine, context)
                if constant is None:
                    return None
                op_index = -1 - op_index
            else:
                return None
            op = ops[op_index]
            if op == '>':
                return {'minimum': constant, 'exclusiveMinimum': True}
            elif op == '>=':
                return {'minimum': constant, 'exclusiveMinimum': False}
            if op == '<':
                return {'maximum': constant, 'exclusiveMaximum': True}
            elif op == '<=':
                return {'maximum': constant, 'exclusiveMaximum': False}
        elif expr.operator == 'in' and is_dollar(expr.args[0]):
            lst = evaluate_constant(expr.args[1], engine, context)
            if isinstance(lst, tuple):
                return {'enum': list(lst)}

        elif (expr.operator == '.' and is_dollar(expr.args[0]) and
                isinstance(expr.args[1], expressions.Function)):
            func = expr.args[1]
            if func.name == 'matches':
                constant = evaluate_constant(func.args[0], engine, context)
                if constant is not None:
                    return {'pattern': constant}


def evaluate_constant(expr, engine, context):
    """Evaluate yaql expression into constant value if possible"""
    if isinstance(expr, expressions.Constant):
        return expr.value
    context = context.create_child_context()
    trap = utils.create_marker('trap')
    context['$'] = trap

    @specs.parameter('name', yaqltypes.StringConstant())
    @specs.name('#get_context_data')
    def get_context_data(name, context):
        res = context[name]
        if res is trap:
            raise yaql_exceptions.ResolutionError()
        return res

    context.register_function(get_context_data)

    try:
        return expressions.Statement(expr, engine).evaluate(context=context)
    except yaql_exceptions.YaqlException:
        return None
