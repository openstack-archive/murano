#    Copyright (c) 2014 #Mirantis, Inc.
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

import contextlib
import re
import sys
import types
import uuid

import eventlet.greenpool
import eventlet.greenthread
import yaql.language.exceptions
import yaql.language.expressions
from yaql.language import utils as yaqlutils


from murano.common import utils
from murano.dsl import constants
from murano.dsl import dsl_types

KEYWORD_REGEX = re.compile(r'(?!__)\b[^\W\d]\w*\b')

_threads_sequencer = 0


def evaluate(value, context):
    if isinstance(value, (dsl_types.YaqlExpression,
                          yaql.language.expressions.Statement)):
        return value(context)
    elif isinstance(value, yaqlutils.MappingType):
        return yaqlutils.FrozenDict(
            (evaluate(d_key, context),
             evaluate(d_value, context))
            for d_key, d_value in value.iteritems())
    elif yaqlutils.is_sequence(value):
        return tuple(evaluate(t, context) for t in value)
    elif isinstance(value, yaqlutils.SetType):
        return frozenset(evaluate(t, context) for t in value)
    elif yaqlutils.is_iterable(value):
        return tuple(
            evaluate(t, context)
            for t in yaqlutils.limit_iterable(
                value, constants.ITERATORS_LIMIT))
    elif isinstance(value, dsl_types.MuranoObjectInterface):
        return value.object
    else:
        return value


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
            with contextual(get_context()):
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


def enum(**enums):
    return type('Enum', (), enums)


def get_context():
    current_thread = eventlet.greenthread.getcurrent()
    return getattr(current_thread, '__murano_context', None)


def get_executor(context=None):
    context = context or get_context()
    return context[constants.CTX_EXECUTOR]


def get_class_loader(context=None):
    context = context or get_context()
    return context[constants.CTX_CLASS_LOADER]


def get_type(context=None):
    context = context or get_context()
    return context[constants.CTX_TYPE]


def get_environment(context=None):
    context = context or get_context()
    return context[constants.CTX_ENVIRONMENT]


def get_object_store(context=None):
    context = context or get_context()
    return context[constants.CTX_OBJECT_STORE]


def get_this(context=None):
    context = context or get_context()
    return context[constants.CTX_THIS]


def get_caller_context(context=None):
    context = context or get_context()
    return context[constants.CTX_CALLER_CONTEXT]


def get_attribute_store(context=None):
    context = context or get_context()
    return context[constants.CTX_ATTRIBUTE_STORE]


def get_current_instruction(context=None):
    context = context or get_context()
    return context[constants.CTX_CURRENT_INSTRUCTION]


def get_current_method(context=None):
    context = context or get_context()
    return context[constants.CTX_CURRENT_METHOD]


def get_current_exception(context=None):
    context = context or get_context()
    return context[constants.CTX_CURRENT_EXCEPTION]


def are_property_modifications_allowed(context=None):
    context = context or get_context()
    return context[constants.CTX_ALLOW_PROPERTY_WRITES] or False


def is_keyword(text):
    return KEYWORD_REGEX.match(text) is not None


def get_current_thread_id():
    global _threads_sequencer

    current_thread = eventlet.greenthread.getcurrent()
    thread_id = getattr(current_thread, '__thread_id', None)
    if thread_id is None:
        thread_id = 'T' + str(_threads_sequencer)
        _threads_sequencer += 1
        setattr(current_thread, '__thread_id', thread_id)
    return thread_id


@contextlib.contextmanager
def contextual(ctx):
    current_thread = eventlet.greenthread.getcurrent()
    current_context = getattr(current_thread, '__murano_context', None)
    if ctx:
        setattr(current_thread, '__murano_context', ctx)
    try:
        yield
    finally:
        if current_context:
            setattr(current_thread, '__murano_context', current_context)
        elif hasattr(current_thread, '__murano_context'):
            delattr(current_thread, '__murano_context')
