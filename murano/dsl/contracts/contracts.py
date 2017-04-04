#    Copyright (c) 2016 Mirantis, Inc.
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

import copy

from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl.contracts import basic
from murano.dsl.contracts import check
from murano.dsl.contracts import instances
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import yaql_integration


CONTRACT_METHODS = [
    basic.String,
    basic.Bool,
    basic.Int,
    basic.NotNull,
    check.Check,
    instances.Class,
    instances.Template,
    instances.Owned,
    instances.NotOwned
]


class Contract(object):
    def __init__(self, spec, declaring_type):
        self._spec = spec
        self._runtime_version = declaring_type.package.runtime_version

    @property
    def spec(self):
        return self._spec

    @staticmethod
    def _get_contract_factory(cls, action_func):
        def payload(context, value, *args, **kwargs):
            instance = object.__new__(cls)
            instance.value = value
            instance.context = context
            instance.__init__(*args, **kwargs)
            return action_func(instance)

        name = yaql_integration.CONVENTION.convert_function_name(cls.name)
        try:
            init_spec = specs.get_function_definition(
                helpers.function(cls.__init__),
                name=name, method=True, convention=yaql_integration.CONVENTION)
        except AttributeError:
            init_spec = specs.get_function_definition(
                lambda self: None,
                name=name, method=True)

        init_spec.parameters['self'] = specs.ParameterDefinition(
            'self', yaqltypes.PythonType(object, nullable=True), 0)
        init_spec.insert_parameter(specs.ParameterDefinition(
            '?1', yaqltypes.Context(), 0))
        init_spec.payload = payload
        return init_spec

    @staticmethod
    def _prepare_context(runtime_version, action):
        context = yaql_integration.create_context(
            runtime_version).create_child_context()
        for cls in CONTRACT_METHODS:
            context.register_function(Contract._get_contract_factory(
                cls, action))
        return context

    @staticmethod
    @helpers.memoize
    def _prepare_transform_context(runtime_version, finalize):
        if finalize:
            def action(c):
                c.value = c.transform()
                return c.finalize()
        else:
            def action(c):
                return c.transform()
        return Contract._prepare_context(
            runtime_version, action)

    @staticmethod
    @helpers.memoize
    def _prepare_validate_context(runtime_version):
        return Contract._prepare_context(
            runtime_version, lambda c: c.validate())

    @staticmethod
    @helpers.memoize
    def _prepare_check_type_context(runtime_version):
        return Contract._prepare_context(
            runtime_version, lambda c: c.check_type())

    @staticmethod
    @helpers.memoize
    def _prepare_schema_generation_context(runtime_version):
        context = Contract._prepare_context(
            runtime_version, lambda c: c.generate_schema())

        @specs.name('#finalize')
        def finalize(obj):
            if isinstance(obj, dict):
                obj.pop('_notNull', None)
            return obj

        context.register_function(finalize)
        return context

    @staticmethod
    @helpers.memoize
    def _prepare_finalize_context(runtime_version):
        return Contract._prepare_context(
            runtime_version, lambda c: c.finalize())

    def _map_dict(self, data, spec, context, path):
        if data is None or data is dsl.NO_VALUE:
            data = {}
        if not isinstance(data, utils.MappingType):
            raise exceptions.ContractViolationException(
                'Value {0} is not of a dictionary type'.format(
                    helpers.format_scalar(data)))
        if not spec:
            return data
        result = {}
        yaql_key = None
        for key, value in spec.items():
            if isinstance(key, dsl_types.YaqlExpression):
                if yaql_key is not None:
                    raise exceptions.DslContractSyntaxError(
                        'Dictionary contract '
                        'cannot have more than one expression key')
                else:
                    yaql_key = key
            else:
                result[key] = self._map(
                    data.get(key), value, context, '{0}[{1}]'.format(
                        path, helpers.format_scalar(key)))

        if yaql_key is not None:
            yaql_value = spec[yaql_key]
            for key, value in data.items():
                if key in result:
                    continue
                key = self._map(key, yaql_key, context, path)
                result[key] = self._map(
                    value, yaql_value, context, '{0}[{1}]'.format(
                        path, helpers.format_scalar(key)))

        return utils.FrozenDict(result)

    def _map_list(self, data, spec, context, path):
        if utils.is_iterator(data):
            data = list(data)
        elif not utils.is_sequence(data):
            if data is None or data is dsl.NO_VALUE:
                data = []
            else:
                data = [data]
        if len(spec) < 1:
            return data
        shift = 0
        max_length = -1
        min_length = 0
        if isinstance(spec[-1], int):
            min_length = spec[-1]
            shift += 1
        if len(spec) >= 2 and isinstance(spec[-2], int):
            max_length = min_length
            min_length = spec[-2]
            shift += 1

        if max_length >= 0 and not min_length <= len(data) <= max_length:
            raise exceptions.ContractViolationException(
                'Array length {0} is not within [{1}..{2}] range'.format(
                    len(data), min_length, max_length))
        elif not min_length <= len(data):
            raise exceptions.ContractViolationException(
                'Array length {0} must not be less than {1}'.format(
                    len(data), min_length))

        def map_func():
            for index, item in enumerate(data):
                spec_item = (
                    spec[-1 - shift]
                    if index >= len(spec) - shift
                    else spec[index]
                )
                yield self._map(
                    item, spec_item, context, '{0}[{1}]'.format(path, index))

        return tuple(map_func())

    def _map_scalar(self, data, spec):
        if data != spec:
            raise exceptions.ContractViolationException(
                'Value {0} is not equal to {1}'.format(
                    helpers.format_scalar(data), spec))
        else:
            return data

    def _map(self, data, spec, context, path):
        if helpers.is_passkey(data):
            return data
        child_context = context.create_child_context()
        if isinstance(spec, dsl_types.YaqlExpression):
            child_context[''] = data
            try:
                result = spec(context=child_context)
                return result
            except exceptions.ContractViolationException as e:
                e.path = path
                raise
        elif isinstance(spec, utils.MappingType):
            return self._map_dict(data, spec, child_context, path)
        elif utils.is_sequence(spec):
            return self._map_list(data, spec, child_context, path)
        else:
            return self._map_scalar(data, spec)

    def _execute(self, base_context_func, data, context, default, **kwargs):
        # TODO(ativelkov, slagun): temporary fix, need a better way of handling
        # composite defaults
        # A bug (#1313694) has been filed

        if data is dsl.NO_VALUE:
            data = helpers.evaluate(default, context)

        if helpers.is_passkey(data):
            return data

        contract_context = base_context_func(
            self._runtime_version).create_child_context()
        contract_context['root_context'] = context
        for key, value in kwargs.items():
            contract_context[key] = value
        contract_context[constants.CTX_NAMES_SCOPE] = \
            context[constants.CTX_NAMES_SCOPE]
        return self._map(data, self._spec, contract_context, '')

    def transform(self, data, context, this, owner, default, calling_type,
                  finalize=True):
        return self._execute(
            lambda runtime_version: self._prepare_transform_context(
                runtime_version, finalize), data, context, default,
            this=this, owner=owner, calling_type=calling_type)

    def validate(self, data, context, default, calling_type):
        self._execute(self._prepare_validate_context,
                      data, context, default, calling_type=calling_type)
        return True

    def check_type(self, data, context, default, calling_type):
        if helpers.is_passkey(data):
            return False
        try:
            self._execute(self._prepare_check_type_context,
                          data, context, default, calling_type=calling_type)
            return True
        except exceptions.ContractViolationException:
            return False

    def finalize(self, data, context, calling_type):
        return self._execute(
            self._prepare_finalize_context,
            data, context, None, calling_type=calling_type)

    @staticmethod
    def generate_expression_schema(expression, context, runtime_version,
                                   initial_schema=None):
        if initial_schema is None:
            initial_schema = {}
        else:
            initial_schema = copy.deepcopy(initial_schema)

        contract_context = Contract._prepare_schema_generation_context(
            runtime_version).create_child_context()

        contract_context['root_context'] = context
        contract_context[constants.CTX_NAMES_SCOPE] = \
            context[constants.CTX_NAMES_SCOPE]
        contract_context['$'] = initial_schema
        return expression(context=contract_context)
