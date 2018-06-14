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

from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import yaql_functions
from murano.dsl import yaql_integration


def _prepare_context():
    @specs.parameter('name', yaqltypes.StringConstant())
    def get_context_data(context, name):
        root_context = context['#root_context']

        def set_data(value):
            if not name or name == '$' or name == '$this':
                raise ValueError('Cannot assign to {0}'.format(name))
            ctx = root_context
            while constants.CTX_VARIABLE_SCOPE not in ctx:
                ctx = ctx.parent
            ctx[name] = value

        return _Property(lambda: root_context[name], set_data)

    @specs.parameter('this', _Property)
    @specs.parameter('key', yaqltypes.Keyword())
    def attribution(context, this, key):
        def setter(src_property, value):
            src = src_property.get()
            if isinstance(src, utils.MappingType):
                src_property.set(
                    utils.FrozenDict(
                        itertools.chain(
                            src.items(),
                            ((key, value),))))
            elif isinstance(src, dsl_types.MuranoObject):
                src.set_property(key, value, context['#root_context'])
            elif isinstance(src, (
                    dsl_types.MuranoTypeReference,
                    dsl_types.MuranoType)):
                if isinstance(src, dsl_types.MuranoTypeReference):
                    mc = src.type
                else:
                    mc = src
                helpers.get_executor().set_static_property(
                    mc, key, value, context['#root_context'])
            else:
                raise ValueError(
                    'attribution may only be applied to '
                    'objects and dictionaries')

        def getter(src):
            if isinstance(src, utils.MappingType):
                return src.get(key, {})
            elif isinstance(src, dsl_types.MuranoObject):
                try:
                    return src.get_property(key, context['#root_context'])
                except exceptions.UninitializedPropertyAccessError:
                    return {}
            elif isinstance(src, (
                    dsl_types.MuranoTypeReference,
                    dsl_types.MuranoType)):
                if isinstance(src, dsl_types.MuranoTypeReference):
                    mc = src.type
                else:
                    mc = src
                return helpers.get_executor().get_static_property(
                    mc, key, context['#root_context'])
            else:
                raise ValueError(
                    'attribution may only be applied to '
                    'objects and dictionaries')

        return _Property(
            lambda: getter(this.get()),
            lambda value: setter(this, value))

    @specs.parameter('this', _Property)
    @specs.parameter('index', yaqltypes.Lambda(with_context=True))
    def indexation(context, this, index):
        index = index(context['#root_context'])

        def getter(src):
            if utils.is_sequence(src):
                return src[index]
            else:
                raise ValueError('indexation may only be applied to lists')

        def setter(src_property, value):
            src = src_property.get()
            if utils.is_sequence(src):
                src_property.set(src[:index] + (value,) + src[index + 1:])
            elif isinstance(src, utils.MappingType):
                attribution(context, src_property, index).set(value)

        if isinstance(index, int):
            return _Property(
                lambda: getter(this.get()),
                lambda value: setter(this, value))
        else:
            return attribution(context, this, index)

    def _wrap_type_reference(tr, context):
        return _Property(
            lambda: tr, context['#self']._invalid_target)

    @specs.parameter('prefix', yaqltypes.Keyword())
    @specs.parameter('name', yaqltypes.Keyword())
    @specs.name('#operator_:')
    def ns_resolve(context, prefix, name):
        return _wrap_type_reference(
            yaql_functions.ns_resolve(context, prefix, name), context)

    @specs.parameter('name', yaqltypes.Keyword())
    @specs.name('#unary_operator_:')
    def ns_resolve_unary(context, name):
        return _wrap_type_reference(
            yaql_functions.ns_resolve_unary(context, name), context)

    @specs.parameter('object_', dsl_types.MuranoObject)
    def type_(context, object_):
        return _wrap_type_reference(yaql_functions.type_(object_), context)

    @specs.name('type')
    @specs.parameter('cls', dsl.MuranoTypeParameter())
    def type_from_name(context, cls):
        return _wrap_type_reference(cls, context)

    res_context = yaql_integration.create_empty_context()
    res_context.register_function(get_context_data, '#get_context_data')
    res_context.register_function(attribution, '#operator_.')
    res_context.register_function(indexation, '#indexer')
    res_context.register_function(ns_resolve)
    res_context.register_function(ns_resolve_unary)
    res_context.register_function(type_)
    res_context.register_function(type_from_name)
    return res_context


class _Property(object):
    def __init__(self, getter, setter):
        self._getter = getter
        self._setter = setter

    def get(self):
        return self._getter()

    def set(self, value):
        self._setter(value)


class LhsExpression(object):
    lhs_context = _prepare_context()

    def __init__(self, expression):
        self._expression = expression

    def _invalid_target(self, *args, **kwargs):
        raise exceptions.InvalidLhsTargetError(self._expression)

    def __call__(self, value, context):
        new_context = LhsExpression.lhs_context.create_child_context()
        new_context[''] = context['$']
        new_context['#root_context'] = context
        new_context['#self'] = self
        for name in (constants.CTX_NAMES_SCOPE,):
            new_context[name] = context[name]
        prop = self._expression(context=new_context)
        if not isinstance(prop, _Property):
            self._invalid_target()
        prop.set(value)
