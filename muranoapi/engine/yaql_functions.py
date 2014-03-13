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

import eventlet
import itertools
import types

from yaql import context as y_context
import yaql.exceptions

from muranoapi.engine import exceptions
from muranoapi.engine import helpers
from muranoapi.engine import objects


def _resolve(name, obj):
    @y_context.EvalArg('this', objects.MuranoObject)
    @y_context.ContextAware()
    def invoke(context, this, *args):
        try:
            executor = helpers.get_executor(context)
            murano_class = helpers.get_type(context)
            return executor.invoke_method(name, this, context,
                                          murano_class, *args)
        except exceptions.NoMethodFound:
            raise yaql.exceptions.YaqlExecutionException()
        except exceptions.AmbiguousMethodName:
            raise yaql.exceptions.YaqlExecutionException()

    if not isinstance(obj, objects.MuranoObject):
        return None

    return invoke


@y_context.EvalArg('value', objects.MuranoObject)
def _id(value):
    return value.object_id


@y_context.EvalArg('value', objects.MuranoObject)
@y_context.EvalArg('type', str)
@y_context.ContextAware()
def _cast(context, value, type):
    if not '.' in type:
        murano_class = context.get_data('$?type')
        type = murano_class.namespace_resolver.resolve_name(type)
    class_loader = helpers.get_class_loader(context)
    return value.cast(class_loader.get_class(type))


@y_context.EvalArg('name', str)
@y_context.ContextAware()
def _new(context, name, *args):
    murano_class = helpers.get_type(context)
    name = murano_class.namespace_resolver.resolve_name(name)
    parameters = {}
    arg_values = [t() for t in args]
    if len(arg_values) == 1 and isinstance(
            arg_values[0], types.DictionaryType):
        parameters = arg_values[0]
    elif len(arg_values) > 0:
        for p in arg_values:
            if not isinstance(p, types.TupleType) or \
                    not isinstance(p[0], types.StringType):
                    raise SyntaxError()
            parameters[p[0]] = p[1]

    object_store = helpers.get_object_store(context)
    class_loader = helpers.get_class_loader(context)
    new_context = y_context.Context(parent_context=context)
    for key, value in parameters.iteritems():
        new_context.set_data(value, key)
    return class_loader.get_class(name).new(
        None, object_store, new_context, parameters=parameters)


@y_context.EvalArg('value', objects.MuranoObject)
def _super(value):
    return [value.cast(type) for type in value.type.parents]


@y_context.EvalArg('value', objects.MuranoObject)
def _super2(value, func):
    return itertools.imap(func, _super(value))


@y_context.EvalArg('value', objects.MuranoObject)
def _psuper2(value, func):
    helpers.parallel_select(_super(value), func)


@y_context.EvalArg('value', object)
def _require(value):
    if value is None:
        raise ValueError()
    return value


@y_context.EvalArg('obj', objects.MuranoObject)
@y_context.EvalArg('class_name', str)
@y_context.ContextAware()
def _get_container(context, obj, class_name):
    namespace_resolver = helpers.get_type(context).namespace_resolver
    class_loader = helpers.get_class_loader(context)
    class_name = namespace_resolver.resolve_name(class_name)
    murano_class = class_loader.get_class(class_name)
    p = obj.parent
    while p is not None:
        if murano_class.is_compatible(p):
            return p
        p = p.parent
    return None


@y_context.EvalArg('seconds', (int, float))
def _sleep(seconds):
    eventlet.sleep(seconds)


def register(context):
    context.register_function(_resolve, '#resolve')
    context.register_function(_cast, 'cast')
    context.register_function(_new, 'new')
    context.register_function(_id, 'id')
    context.register_function(_super2, 'super')
    context.register_function(_psuper2, 'psuper')
    context.register_function(_super, 'super')
    context.register_function(_require, 'require')
    context.register_function(_get_container, 'find')
    context.register_function(_sleep, 'sleep')
