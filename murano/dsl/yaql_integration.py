#    Copyright (c) 2015 Mirantis, Inc.
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

import inspect

from yaql.language import contexts
from yaql.language import conventions
from yaql.language import factory
from yaql.language import specs
from yaql.language import yaqltypes
from yaql import legacy

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers


LEGACY_ENGINE_OPTIONS = {
    'yaql.limitIterators': constants.ITERATORS_LIMIT,
    'yaql.memoryQuota': constants.EXPRESSION_MEMORY_QUOTA,
    'yaql.iterableDicts': True
}


def _create_engine():
    engine_factory = factory.YaqlFactory()
    engine_factory.insert_operator(
        '.', True, ':', factory.OperatorType.BINARY_LEFT_ASSOCIATIVE, True)
    return engine_factory.create(options=LEGACY_ENGINE_OPTIONS)


@specs.name('#finalize')
def _finalize(obj, context):
    return helpers.evaluate(obj, context)


ENGINE = _create_engine()
CONVENTION = conventions.CamelCaseConvention()
ROOT_CONTEXT = legacy.create_context(
    convention=CONVENTION, finalizer=_finalize)


class ContractedValue(yaqltypes.GenericType):
    def __init__(self, value_spec):
        self._value_spec = value_spec
        self._last_result = False

        super(ContractedValue, self).__init__(
            True, None,
            lambda value, sender, context, *args, **kwargs:
                self._value_spec.validate(
                    value, sender.real_this,
                    context[constants.CTX_ARGUMENT_OWNER]))

    def convert(self, value, *args, **kwargs):
        if value is None:
            return self.converter(value, *args, **kwargs)
        return super(ContractedValue, self).convert(value, *args, **kwargs)


def create_empty_context():
    context = contexts.Context()
    context.register_function(_finalize)
    return context


def create_context():
    return ROOT_CONTEXT.create_child_context()


def choose_yaql_engine(version):
    return ENGINE


def parse(expression, version):
    return choose_yaql_engine(version)(expression)


def call_func(__context, __name, *args, **kwargs):
    return __context(__name, ENGINE)(*args, **kwargs)


def _infer_parameter_type(name, class_name):
    if name == 'context':
        return yaqltypes.Context()
    if name == 'this':
        return dsl.ThisParameterType()
    if name == 'interfaces':
        return dsl.InterfacesParameterType()
    if name == 'yaql_engine':
        return yaqltypes.Engine()

    if name.startswith('__'):
        return _infer_parameter_type(name[2:], class_name)
    if class_name and name.startswith('_{0}__'.format(class_name)):
        return _infer_parameter_type(name[3 + len(class_name):], class_name)


def get_function_definition(func):
    body = func
    param_type_func = lambda name: _infer_parameter_type(name, None)
    is_method = False
    if inspect.ismethod(func):
        is_method = True
        body = func.im_func
        param_type_func = lambda name: _infer_parameter_type(
            name, func.im_class.__name__)
    fd = specs.get_function_definition(
        body, convention=CONVENTION,
        parameter_type_func=param_type_func)
    if is_method:
        fd.is_method = True
        fd.is_function = False
        fd.set_parameter(
            0,
            yaqltypes.PythonType(func.im_class),
            overwrite=True)
    name = getattr(func, '__murano_name', None)
    if name:
        fd.name = name
    fd.insert_parameter(specs.ParameterDefinition(
        '?1', yaqltypes.Context(), 0))

    def payload(__context, *args, **kwargs):
        with helpers.contextual(__context):
            return body(*args, **kwargs)

    fd.payload = payload
    return fd


def build_wrapper_function_definition(murano_method):
    if isinstance(murano_method.body, specs.FunctionDefinition):
        return _build_native_wrapper_function_definition(murano_method)
    else:
        return _build_mpl_wrapper_function_definition(murano_method)


def _build_native_wrapper_function_definition(murano_method):
    @specs.method
    @specs.name(murano_method.name)
    def payload(__context, __sender, *args, **kwargs):
        executor = helpers.get_executor(__context)
        args = tuple(to_mutable(arg) for arg in args)
        kwargs = to_mutable(kwargs)
        return murano_method.invoke(
            executor, __sender, args, kwargs, __context, True)

    return specs.get_function_definition(payload)


def _build_mpl_wrapper_function_definition(murano_method):
    def payload(__context, __sender, *args, **kwargs):
        executor = helpers.get_executor(__context)
        return murano_method.invoke(
            executor, __sender, args, kwargs, __context, True)

    fd = specs.FunctionDefinition(
        murano_method.name, payload, is_function=False, is_method=True)

    for i, (name, arg_spec) in enumerate(
            murano_method.arguments_scheme.iteritems(), 2):
        p = specs.ParameterDefinition(
            name, ContractedValue(arg_spec),
            position=i, default=dsl.NO_VALUE)
        fd.parameters[name] = p

    fd.set_parameter(specs.ParameterDefinition(
        '__context', yaqltypes.Context(), 0))

    fd.set_parameter(specs.ParameterDefinition(
        '__sender', yaqltypes.PythonType(dsl_types.MuranoObject, False), 1))

    return fd


def get_class_factory_definition(cls):
    def payload(__context, __sender, *args, **kwargs):
        assert __sender is None
        args = tuple(to_mutable(arg) for arg in args)
        kwargs = to_mutable(kwargs)
        with helpers.contextual(__context):
            return cls(*args, **kwargs)

    if hasattr(cls.__init__, 'im_func'):
        fd = specs.get_function_definition(
            cls.__init__.im_func,
            parameter_type_func=lambda name: _infer_parameter_type(
                name, cls.__init__.im_class.__name__))
    else:
        fd = specs.get_function_definition(lambda self: None)
        fd.meta[constants.META_NO_TRACE] = True
    fd.insert_parameter(specs.ParameterDefinition(
        '?1', yaqltypes.Context(), position=0))
    fd.is_method = True
    fd.is_function = False
    fd.name = '__init__'
    fd.payload = payload
    return fd


def filter_parameters(__fd, *args, **kwargs):
    if '*' not in __fd.parameters:
        position_args = 0
        for p in __fd.parameters.itervalues():
            if p.position is not None:
                position_args += 1
        args = args[:position_args]
    kwargs = kwargs.copy()
    for name in kwargs.keys():
        if not helpers.is_keyword(name):
            del kwargs[name]
    if '**' not in __fd.parameters:
        for name in kwargs.keys():
            if name not in __fd.parameters:
                del kwargs[name]
    return args, kwargs


def filter_parameters_dict(parameters):
    parameters = parameters.copy()
    for name in parameters.keys():
        if not helpers.is_keyword(name):
            del parameters[name]
    return parameters


def to_mutable(obj):
    return dsl.to_mutable(obj, ENGINE)
