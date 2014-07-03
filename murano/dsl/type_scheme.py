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

import sys
import types
import uuid

import yaql.context

from murano.dsl import exceptions
import murano.dsl.helpers
import murano.dsl.murano_object
import murano.dsl.yaql_expression as yaql_expression


NoValue = object()


class TypeScheme(object):
    class ObjRef(object):
        def __init__(self, object_id):
            self.object_id = object_id

    def __init__(self, spec):
        self._spec = spec

    @staticmethod
    def prepare_context(root_context, this, owner, object_store,
                        namespace_resolver, default):
        def _int(value):
            value = value()
            if value is NoValue:
                value = default
            if value is None:
                return None
            try:
                return int(value)
            except Exception:
                raise exceptions.ContractViolationException(
                    'Value {0} violates int() contract'.format(value))

        def _string(value):
            value = value()
            if value is NoValue:
                value = default
            if value is None:
                return None
            try:
                return unicode(value)
            except Exception:
                raise exceptions.ContractViolationException(
                    'Value {0} violates string() contract'.format(value))

        def _bool(value):
            value = value()
            if value is NoValue:
                value = default
            if value is None:
                return None
            return True if value else False

        def _not_null(value):
            value = value()

            if isinstance(value, TypeScheme.ObjRef):
                return value

            if value is None:
                raise exceptions.ContractViolationException(
                    'null value violates notNull() contract')
            return value

        def _error():
            raise exceptions.ContractViolationException('error() contract')

        def _check(value, predicate):
            value = value()
            if isinstance(value, TypeScheme.ObjRef) or predicate(value):
                return value
            else:
                raise exceptions.ContractViolationException(
                    "Value {0} doesn't match predicate".format(value))

        @yaql.context.EvalArg('obj', arg_type=(
            murano.dsl.murano_object.MuranoObject,
            TypeScheme.ObjRef,
            types.NoneType
        ))
        def _owned(obj):
            if isinstance(obj, TypeScheme.ObjRef):
                return obj

            if obj is None:
                return None

            p = obj.owner
            while p is not None:
                if p is this:
                    return obj
                p = p.owner

            raise exceptions.ContractViolationException(
                'Object {0} violates owned() contract'.format(
                    obj.object_id))

        @yaql.context.EvalArg('obj', arg_type=(
            murano.dsl.murano_object.MuranoObject,
            TypeScheme.ObjRef,
            types.NoneType
        ))
        def _not_owned(obj):
            if isinstance(obj, TypeScheme.ObjRef):
                return obj

            if obj is None:
                return None

            try:
                _owned(obj)
            except exceptions.ContractViolationException:
                return obj
            else:
                raise exceptions.ContractViolationException(
                    'Object {0} violates notOwned() contract'.format(
                        obj.object_id))

        @yaql.context.EvalArg('name', arg_type=str)
        def _class(value, name):
            return _class2(value, name, None)

        @yaql.context.EvalArg('name', arg_type=str)
        @yaql.context.EvalArg('default_name', arg_type=(str, types.NoneType))
        def _class2(value, name, default_name):
            name = namespace_resolver.resolve_name(name)
            if not default_name:
                default_name = name
            else:
                default_name = namespace_resolver.resolve_name(default_name)
            value = value()
            class_loader = murano.dsl.helpers.get_class_loader(root_context)
            murano_class = class_loader.get_class(name)
            if not murano_class:
                raise exceptions.NoClassFound(
                    'Class {0} cannot be found'.format(name))
            if value is None:
                return None
            if isinstance(value, murano.dsl.murano_object.MuranoObject):
                obj = value
            elif isinstance(value, types.DictionaryType):
                if '?' not in value:
                    new_value = {'?': {
                        'id': uuid.uuid4().hex,
                        'type': default_name
                    }}
                    new_value.update(value)
                    value = new_value

                obj = object_store.load(value, owner, root_context,
                                        defaults=default)
            elif isinstance(value, types.StringTypes):
                obj = object_store.get(value)
                if obj is None:
                    if not object_store.initializing:
                        raise exceptions.NoObjectFoundError(value)
                    else:
                        return TypeScheme.ObjRef(value)
            else:
                raise exceptions.ContractViolationException(
                    'Value {0} cannot be represented as class {1}'.format(
                        value, name))
            if not murano_class.is_compatible(obj):
                raise exceptions.ContractViolationException(
                    'Object of type {0} is not compatible with '
                    'requested type {1}'.format(obj.type.name, name))
            return obj

        @yaql.context.EvalArg('prefix', str)
        @yaql.context.EvalArg('name', str)
        def _validate(prefix, name):
            return namespace_resolver.resolve_name(
                '%s:%s' % (prefix, name))

        context = yaql.context.Context(parent_context=root_context)
        context.register_function(_validate, '#validate')
        context.register_function(_int, 'int')
        context.register_function(_string, 'string')
        context.register_function(_bool, 'bool')
        context.register_function(_check, 'check')
        context.register_function(_not_null, 'notNull')
        context.register_function(_error, 'error')
        context.register_function(_class, 'class')
        context.register_function(_class2, 'class')
        context.register_function(_owned, 'owned')
        context.register_function(_not_owned, 'notOwned')
        return context

    def _map_dict(self, data, spec, context):
        if data is None or data is NoValue:
            data = {}
        if not isinstance(data, types.DictionaryType):
            raise exceptions.ContractViolationException(
                'Supplied is not of a dictionary type')
        if not spec:
            return data
        result = {}
        yaql_key = None
        for key, value in spec.iteritems():
            if isinstance(key, yaql_expression.YaqlExpression):
                if yaql_key is not None:
                    raise exceptions.DslContractSyntaxError(
                        'Dictionary contract '
                        'cannot have more than one expression keys')
                else:
                    yaql_key = key
            else:
                result[key] = self._map(data.get(key), value, context)

        if yaql_key is not None:
            yaql_value = spec[yaql_key]
            for key, value in data.iteritems():
                if key in result:
                    continue
                result[self._map(key, yaql_key, context)] = \
                    self._map(value, yaql_value, context)

        return result

    def _map_list(self, data, spec, context):
        if not isinstance(data, types.ListType):
            if data is None or data is NoValue:
                data = []
            else:
                data = [data]
        if len(spec) < 1:
            return data
        result = []
        shift = 0
        max_length = sys.maxint
        min_length = 0
        if isinstance(spec[-1], types.IntType):
            min_length = spec[-1]
            shift += 1
        if len(spec) >= 2 and isinstance(spec[-2], types.IntType):
            max_length = min_length
            min_length = spec[-2]
            shift += 1

        if not min_length <= len(data) <= max_length:
            raise exceptions.ContractViolationException(
                'Array length {0} is not within [{1}..{2}] range'.format(
                    len(data), min_length, max_length))

        for index, item in enumerate(data):
            spec_item = spec[-1 - shift] \
                if index >= len(spec) - shift else spec[index]
            result.append(self._map(item, spec_item, context))
        return result

    def _map_scalar(self, data, spec):
        if data != spec:
            raise exceptions.ContractViolationException(
                'Value {0} is not equal to {1}'.format(data, spec))
        else:
            return data

    def _map(self, data, spec, context):
        child_context = yaql.context.Context(parent_context=context)
        if isinstance(spec, yaql_expression.YaqlExpression):
            child_context.set_data(data)
            return spec.evaluate(context=child_context)
        elif isinstance(spec, types.DictionaryType):
            return self._map_dict(data, spec, child_context)
        elif isinstance(spec, types.ListType):
            return self._map_list(data, spec, child_context)
        elif isinstance(spec, (types.IntType,
                               types.StringTypes,
                               types.NoneType)):
            return self._map_scalar(data, spec)

    def __call__(self, data, context, this, owner, object_store,
                 namespace_resolver, default):
        # TODO(ativelkov, slagun): temporary fix, need a better way of handling
        # composite defaults
        # A bug (#1313694) has been filed

        if data is NoValue:
            data = default

        context = self.prepare_context(
            context, this, owner, object_store, namespace_resolver, default)
        return self._map(data, self._spec, context)
