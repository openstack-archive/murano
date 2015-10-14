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

import eventlet
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import linked_context


@specs.parameter('value', dsl_types.MuranoObject)
def id_(value):
    return value.object_id


@specs.parameter('value', dsl_types.MuranoObject)
@specs.parameter('type__', dsl.MuranoTypeName())
@specs.parameter('version_spec', yaqltypes.String(True))
def cast(context, value, type__, version_spec=None):
    return helpers.cast(
        value, type__.murano_class.name,
        version_spec or helpers.get_type(context))


@specs.parameter('__type_name', dsl.MuranoTypeName())
@specs.parameter('__extra', utils.MappingType)
@specs.parameter('__owner', dsl_types.MuranoObject)
@specs.parameter('__object_name', yaqltypes.String(True))
def new(__context, __type_name, __owner=None, __object_name=None, __extra=None,
        **parameters):
    object_store = helpers.get_object_store(__context)
    new_context = __context.create_child_context()
    for key, value in parameters.iteritems():
        if helpers.is_keyword(key):
            new_context[key] = value
    return __type_name.murano_class.new(
        __owner, object_store, name=__object_name)(new_context, **parameters)


@specs.parameter('type_name', dsl.MuranoTypeName())
@specs.parameter('parameters', utils.MappingType)
@specs.parameter('extra', utils.MappingType)
@specs.parameter('owner', dsl_types.MuranoObject)
@specs.parameter('object_name', yaqltypes.String(True))
@specs.name('new')
def new_from_dict(type_name, context, parameters,
                  owner=None, object_name=None, extra=None):
    return new(context, type_name, owner, object_name, extra,
               **helpers.filter_parameters_dict(parameters))


@specs.parameter('sender', dsl_types.MuranoObject)
@specs.parameter('func', yaqltypes.Lambda())
def super_(context, sender, func=None):
    cast_type = helpers.get_type(context)
    if func is None:
        return [sender.cast(type) for type in cast_type.parents(
            sender.real_this.type)]
    return itertools.imap(func, super_(context, sender))


@specs.parameter('value', dsl_types.MuranoObject)
@specs.parameter('func', yaqltypes.Lambda())
def psuper(context, value, func=None):
    if func is None:
        return super_(context, value)
    return helpers.parallel_select(super_(context, value), func)


@specs.extension_method
def require(value):
    if value is None:
        raise ValueError('Required value is missing')
    return value


@specs.parameter('obj', dsl_types.MuranoObject)
@specs.parameter('murano_class_ref', dsl.MuranoTypeName())
@specs.extension_method
def find(obj, murano_class_ref):
    p = obj.owner
    while p is not None:
        if murano_class_ref.murano_class.is_compatible(p):
            return p
        p = p.owner
    return None


@specs.parameter('seconds', yaqltypes.Number())
def sleep_(seconds):
    eventlet.sleep(seconds)


@specs.parameter('object_', dsl_types.MuranoObject)
def type_(object_):
    return object_.type.name


@specs.parameter('object_', dsl_types.MuranoObject)
def name(object_):
    return object_.name


@specs.parameter('obj', dsl_types.MuranoObject)
@specs.parameter('property_name', yaqltypes.Keyword())
@specs.name('#operator_.')
def obj_attribution(context, obj, property_name):
    return obj.get_property(property_name, context)


@specs.parameter('sender', dsl_types.MuranoObject)
@specs.parameter('expr', yaqltypes.Lambda(method=True))
@specs.inject('operator', yaqltypes.Super(with_context=True))
@specs.name('#operator_.')
def op_dot(context, sender, expr, operator):
    executor = helpers.get_executor(context)
    type_context = executor.context_manager.create_class_context(sender.type)
    obj_context = executor.context_manager.create_object_context(sender)
    ctx2 = linked_context.link(
        linked_context.link(context, type_context),
        obj_context)
    return operator(ctx2, sender, expr)


@specs.parameter('prefix', yaqltypes.Keyword())
@specs.parameter('name', yaqltypes.Keyword())
@specs.name('#operator_:')
def ns_resolve(context, prefix, name):
    murano_type = helpers.get_type(context)
    return dsl_types.MuranoClassReference(
        helpers.get_class(
            murano_type.namespace_resolver.resolve_name(
                prefix + ':' + name), context))


@specs.parameter('obj1', dsl_types.MuranoObject, nullable=True)
@specs.parameter('obj2', dsl_types.MuranoObject, nullable=True)
@specs.name('*equal')
def equal(obj1, obj2):
    return obj1 is obj2


@specs.parameter('obj1', dsl_types.MuranoObject, nullable=True)
@specs.parameter('obj2', dsl_types.MuranoObject, nullable=True)
@specs.name('*not_equal')
def not_equal(obj1, obj2):
    return obj1 is not obj2


def register(context, runtime_version):
    context.register_function(cast)
    context.register_function(new)
    context.register_function(new_from_dict)
    context.register_function(id_)
    context.register_function(super_)
    context.register_function(psuper)
    context.register_function(require)
    context.register_function(find)
    context.register_function(sleep_)
    context.register_function(type_)
    context.register_function(name)
    context.register_function(obj_attribution)
    context.register_function(op_dot)
    context.register_function(ns_resolve)
    context.register_function(equal)
    context.register_function(not_equal)

    if runtime_version <= constants.RUNTIME_VERSION_1_1:
        context2 = context.create_child_context()
        for t in ('id', 'cast', 'super', 'psuper', 'type'):
            for spec in utils.to_extension_method(t, context):
                context2.register_function(spec)
        return context2
    return context
