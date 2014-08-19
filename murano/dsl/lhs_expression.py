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

import types

import yaql
import yaql.context
import yaql.expressions

import murano.dsl.murano_object as murano_object
import murano.dsl.type_scheme as type_scheme
import murano.dsl.yaql_expression as yaql_expression


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
        if isinstance(expression, (yaql_expression.YaqlExpression,
                                   yaql.expressions.Expression)):
            self._expression = expression
        else:
            self._expression = yaql.parse(str(expression))
        self._current_obj = None
        self._current_obj_name = None

    def _create_context(self, root_context, murano_class):
        def _evaluate(thing):
            if isinstance(thing, yaql.expressions.Expression.Callable):
                thing.yaql_context = root_context
                thing = thing()
            return thing

        def _get_value(src, key):
            key = _evaluate(key)
            if isinstance(src, types.DictionaryType):
                return src.get(key)
            elif isinstance(src, types.ListType) and isinstance(
                    key, types.IntType):
                return src[key]
            elif isinstance(src, murano_object.MuranoObject) and isinstance(
                    key, types.StringTypes):
                self._current_obj = src
                self._current_obj_name = key
                return src.get_property(key, murano_class)
            else:
                raise TypeError()

        def _set_value(src, key, value):
            key = _evaluate(key)
            if isinstance(src, types.DictionaryType):
                old_value = src.get(key, type_scheme.NoValue)
                src[key] = value
                if self._current_obj is not None:
                    try:
                        p_value = self._current_obj.get_property(
                            self._current_obj_name, murano_class)
                        self._current_obj.set_property(
                            self._current_obj_name, p_value, murano_class)
                    except Exception as e:
                        if old_value is not type_scheme.NoValue:
                            src[key] = old_value
                        else:
                            src.pop(key, None)
                        raise e
            elif isinstance(src, types.ListType) and isinstance(
                    key, types.IntType):
                old_value = src[key]
                src[key] = value
                if self._current_obj is not None:
                    try:
                        p_value = self._current_obj.get_property(
                            self._current_obj_name, murano_class)
                        self._current_obj.set_property(
                            self._current_obj_name, p_value, murano_class)
                    except Exception as e:
                        src[key] = old_value
                        raise e

            elif isinstance(src, murano_object.MuranoObject) and isinstance(
                    key, types.StringTypes):
                src.set_property(key, value, murano_class)
            else:
                raise TypeError()

        def get_context_data(path):
            path = path()

            def set_data(value):
                if not path or path == '$' or path == '$this':
                    raise ValueError()
                root_context.set_data(value, path)

            return LhsExpression.Property(
                lambda: root_context.get_data(path), set_data)

        @yaql.context.EvalArg('this', arg_type=LhsExpression.Property)
        def attribution(this, arg_name):
            arg_name = arg_name()
            return LhsExpression.Property(
                lambda: _get_value(this.get(), arg_name),
                lambda value: _set_value(this.get(), arg_name, value))

        @yaql.context.EvalArg("this", LhsExpression.Property)
        def indexation(this, index):
            index = _evaluate(index)

            return LhsExpression.Property(
                lambda: _get_value(this.get(), index),
                lambda value: _set_value(this.get(), index, value))

        context = yaql.context.Context()
        context.register_function(get_context_data, '#get_context_data')
        context.register_function(attribution, '#operator_.')
        context.register_function(indexation, "where")
        return context

    def __call__(self, value, context, murano_class):
        new_context = self._create_context(context, murano_class)
        new_context.set_data(context.get_data('$'))
        self._current_obj = None
        self._current_obj_name = None
        property = self._expression.evaluate(context=new_context)
        property.set(value)
