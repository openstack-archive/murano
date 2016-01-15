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
import re
import sys
import types
import uuid

import eventlet.greenpool
import yaql.expressions

from murano.common import utils
import murano.dsl.murano_object
import murano.dsl.yaql_expression as yaql_expression


def serialize(value, memo=None):
    if memo is None:
        memo = set()
    if isinstance(value, types.DictionaryType):
        result = {}
        for d_key, d_value in value.iteritems():
            result[d_key] = serialize(d_value, memo)
        return result
    elif isinstance(value, murano.dsl.murano_object.MuranoObject):
        if value.object_id not in memo:
            memo.add(value.object_id)
            return serialize(value.to_dictionary(), memo)
        else:
            return value.object_id
    elif isinstance(value, types.ListType):
        return [serialize(t, memo) for t in value]
    else:
        return value


def execute_instruction(instruction, action, context):
    old_instruction = context.get_data('$?currentInstruction')
    context.set_data(instruction, '?currentInstruction')
    result = action()
    context.set_data(old_instruction, '?currentInstruction')
    return result


def evaluate(value, context, max_depth=sys.maxint):
    if isinstance(value, yaql.expressions.Expression):
        value = yaql_expression.YaqlExpression(value)

    if isinstance(value, yaql_expression.YaqlExpression):
        func = lambda: evaluate(value.evaluate(context), context, 1)
        if max_depth <= 0:
            return func
        else:
            return execute_instruction(value, func, context)

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


def merge_lists(list1, list2):
    result = []
    for item in list1 + list2:
        exists = False
        for old_item in result:
            if not utils.is_different(item, old_item):
                exists = True
                break
        if not exists:
            result.append(item)
    return result


def merge_dicts(dict1, dict2, max_levels=0):
    result = {}
    for key, value1 in dict1.items():
        result[key] = value1
        if key in dict2:
            value2 = dict2[key]
            if type(value2) != type(value1):
                if (isinstance(value1, types.StringTypes) and
                        isinstance(value2, types.StringTypes)):
                    continue
                raise TypeError()
            if max_levels != 1 and isinstance(value2, types.DictionaryType):
                result[key] = merge_dicts(
                    value1, value2,
                    0 if max_levels == 0 else max_levels - 1)
            elif max_levels != 1 and isinstance(value2, types.ListType):
                result[key] = merge_lists(value1, value2)
            else:
                result[key] = value2
    for key, value1 in dict2.items():
        if key not in result:
            result[key] = value1
    return result


def generate_id():
    return uuid.uuid4().hex


def parallel_select(collection, func, limit=1000):
    # workaround for eventlet issue 232
    # https://github.com/eventlet/eventlet/issues/232
    def wrapper(element):
        try:
            return func(element), False, None
        except Exception as e:
            return e, True, sys.exc_info()[2]

    gpool = eventlet.greenpool.GreenPool(limit)
    result = list(gpool.imap(wrapper, collection))
    try:
        exception = next(t for t in result if t[1])
    except StopIteration:
        return map(lambda t: t[0], result)
    else:
        raise exception[0], None, exception[2]


def to_python_codestyle(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def enum(**enums):
    return type('Enum', (), enums)


def get_executor(context):
    return context.get_data('$?executor')


def get_class_loader(context):
    return context.get_data('$?classLoader')


def get_type(context):
    return context.get_data('$?type')


def get_environment(context):
    return context.get_data('$?environment')


def get_object_store(context):
    return context.get_data('$?objectStore')


def get_this(context):
    return context.get_data('$?this')


def get_caller_context(context):
    return context.get_data('$?callerContext')


def get_attribute_store(context):
    return context.get_data('$?attributeStore')


def get_current_instruction(context):
    return context.get_data('$?currentInstruction')


def get_current_method(context):
    return context.get_data('$?currentMethod')


def get_current_exception(context):
    return context.get_data('$?currentException')
