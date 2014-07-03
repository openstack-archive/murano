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

import itertools
import types

import eventlet
import yaql.context
import yaql.exceptions

import murano.dsl.exceptions as exceptions
import murano.dsl.helpers as helpers
import murano.dsl.murano_object as murano_object


def _resolve(name, obj):
    @yaql.context.EvalArg('this', murano_object.MuranoObject)
    @yaql.context.ContextAware()
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

    if not isinstance(obj, murano_object.MuranoObject):
        return None

    return invoke


@yaql.context.EvalArg('value', murano_object.MuranoObject)
def _id(value):
    return value.object_id


@yaql.context.EvalArg('value', murano_object.MuranoObject)
@yaql.context.EvalArg('type', str)
@yaql.context.ContextAware()
def _cast(context, value, type):
    if '.' not in type:
        murano_class = helpers.get_type(context)
        type = murano_class.namespace_resolver.resolve_name(type)
    class_loader = helpers.get_class_loader(context)
    return value.cast(class_loader.get_class(type))


@yaql.context.EvalArg('name', str)
@yaql.context.ContextAware()
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
    new_context = yaql.context.Context(parent_context=context)
    for key, value in parameters.iteritems():
        new_context.set_data(value, key)
    return class_loader.get_class(name).new(
        None, object_store, new_context, parameters=parameters)


def new(name, context, **kwargs):
    return _new(context, name, lambda: kwargs)


@yaql.context.EvalArg('value', murano_object.MuranoObject)
@yaql.context.ContextAware()
def _super(context, value):
    cast_type = helpers.get_type(context)
    return [value.cast(type) for type in cast_type.parents]


@yaql.context.EvalArg('value', murano_object.MuranoObject)
@yaql.context.ContextAware()
def _super2(context, value, func):
    return itertools.imap(func, _super(context, value))


@yaql.context.EvalArg('value', murano_object.MuranoObject)
@yaql.context.ContextAware()
def _psuper2(context, value, func):
    helpers.parallel_select(_super(context, value), func)


@yaql.context.EvalArg('value', object)
def _require(value):
    if value is None:
        raise ValueError()
    return value


@yaql.context.EvalArg('obj', murano_object.MuranoObject)
@yaql.context.EvalArg('class_name', str)
@yaql.context.ContextAware()
def _get_container(context, obj, class_name):
    namespace_resolver = helpers.get_type(context).namespace_resolver
    class_loader = helpers.get_class_loader(context)
    class_name = namespace_resolver.resolve_name(class_name)
    murano_class = class_loader.get_class(class_name)
    p = obj.owner
    while p is not None:
        if murano_class.is_compatible(p):
            return p
        p = p.owner
    return None


@yaql.context.EvalArg('seconds', (int, float))
def _sleep(seconds):
    eventlet.sleep(seconds)


@yaql.context.EvalArg('value', murano_object.MuranoObject)
def _type(value):
    return value.type.name


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
    context.register_function(_type, 'type')
