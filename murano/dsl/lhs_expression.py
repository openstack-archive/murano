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

from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import yaql_integration


class LhsExpression(object):
    class Property(object):
        def __init__(self, getter, setter):
            self._getter = getter
            self._setter = setter

        def get(self):
            return self._getter()

        def set(self, value):
            self._setter(value)

    def __init__(self, expression):
        self._expression = expression

    def _create_context(self, root_context):
        @specs.parameter('name', yaqltypes.StringConstant())
        def get_context_data(name):

            def set_data(value):
                if not name or name == '$' or name == '$this':
                    raise ValueError('Cannot assign to {0}'.format(name))
                ctx = root_context
                while constants.CTX_VARIABLE_SCOPE not in ctx:
                    ctx = ctx.parent
                ctx[name] = value

            return LhsExpression.Property(
                lambda: root_context[name], set_data)

        @specs.parameter('this', LhsExpression.Property)
        @specs.parameter('key', yaqltypes.Keyword())
        def attribution(this, key):
            def setter(src_property, value):
                src = src_property.get()
                if isinstance(src, utils.MappingType):
                    src_property.set(
                        utils.FrozenDict(
                            itertools.chain(
                                src.iteritems(),
                                ((key, value),))))
                elif isinstance(src, dsl_types.MuranoObject):
                    src.set_property(key, value, root_context)
                else:
                    raise ValueError(
                        'attribution may only be applied to '
                        'objects and dictionaries')

            def getter(src):
                if isinstance(src, utils.MappingType):
                    return src.get(key, {})
                elif isinstance(src, dsl_types.MuranoObject):
                    self._current_obj = src
                    self._current_obj_name = key
                    try:
                        return src.get_property(key, root_context)
                    except exceptions.UninitializedPropertyAccessError:
                        return {}

                else:
                    raise ValueError(
                        'attribution may only be applied to '
                        'objects and dictionaries')

            return LhsExpression.Property(
                lambda: getter(this.get()),
                lambda value: setter(this, value))

        @specs.parameter('this', LhsExpression.Property)
        @specs.parameter('index', yaqltypes.Lambda(with_context=True))
        def indexation(this, index):
            index = index(root_context)

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
                    attribution(src_property, index).set(value)

            if isinstance(index, types.IntType):
                return LhsExpression.Property(
                    lambda: getter(this.get()),
                    lambda value: setter(this, value))
            else:
                return attribution(this, index)

        context = yaql_integration.create_empty_context()
        context.register_function(get_context_data, '#get_context_data')
        context.register_function(attribution, '#operator_.')
        context.register_function(indexation, '#indexer')
        return context

    def __call__(self, value, context):
        new_context = self._create_context(context)
        new_context[''] = context['$']
        self._current_obj = None
        self._current_obj_name = None
        property = self._expression(context=new_context)
        property.set(value)
