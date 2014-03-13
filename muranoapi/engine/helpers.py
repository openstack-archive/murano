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
import types
import uuid

import deep
from eventlet import greenpool
import yaql

from muranoapi.engine import consts
from muranoapi.engine import yaql_expression


def merge_lists(list1, list2):
    result = []
    for item in list1 + list2:
        exists = False
        for old_item in result:
            if deep.diff(item, old_item) is None:
                exists = True
                break
        if not exists:
            result.append(item)
    return result


def merge_dicts(dict1, dict2, max_levels=0):
    result = {}
    for key, value in dict1.items():
        result[key] = value
        if key in dict2:
            other_value = dict2[key]
            if type(other_value) != type(value):
                raise TypeError()
            if max_levels != 1 and isinstance(
                    other_value, types.DictionaryType):
                result[key] = merge_dicts(
                    value, other_value,
                    0 if max_levels == 0 else max_levels - 1)
            elif max_levels != 1 and isinstance(
                    other_value, types.ListType):
                result[key] = merge_lists(value, other_value)
            else:
                result[key] = other_value
    for key, value in dict2.items():
        if key not in result:
            result[key] = value
    return result


def parallel_select(collection, func):
    gp = greenpool.GreenPool()
    return list(gp.imap(func, collection))


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
