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

import collections
import types
import uuid

import yaql

from muranoapi.engine import consts
from muranoapi.engine import yaql_expression


def generate_id():
    return uuid.uuid4().hex


def evaluate(value, context, max_depth=consts.EVALUATION_MAX_DEPTH):
    if isinstance(value, (yaql_expression.YaqlExpression,
                          yaql.expressions.Expression)):
        func = lambda: evaluate(value.evaluate(context), context, 1)
        if max_depth <= 0:
            return func
        else:
            return func()

    elif isinstance(value, types.DictionaryType):
        result = {}
        for d_key, d_value in value.iteritems():
            result[evaluate(d_key, context, max_depth - 1)] = \
                evaluate(d_value, context, max_depth - 1)
        return result
    elif isinstance(value, types.ListType):
        return [evaluate(t, context, max_depth - 1) for t in value]
    elif isinstance(value, types.TupleType):
        return tuple(evaluate(list(value), context, max_depth - 1))
    elif callable(value):
        return value()
    elif isinstance(value, types.StringTypes):
        return value
    elif isinstance(value, collections.Iterable):
        return list(value)
    else:
        return value


def needs_evaluation(value):
    if isinstance(value, (yaql_expression.YaqlExpression,
                          yaql.expressions.Expression)):
        return True
    elif isinstance(value, types.DictionaryType):
        for d_key, d_value in value.iteritems():
            if needs_evaluation(d_value) or needs_evaluation(d_key):
                return True
    elif isinstance(value, types.StringTypes):
        return False
    elif isinstance(value, collections.Iterable):
        for t in value:
            if needs_evaluation(t):
                return True
    return False
