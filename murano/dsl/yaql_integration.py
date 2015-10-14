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

import yaql
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
from murano.dsl import yaql_functions


ENGINE_10_OPTIONS = {
    'yaql.limitIterators': constants.ITERATORS_LIMIT,
    'yaql.memoryQuota': constants.EXPRESSION_MEMORY_QUOTA,
    'yaql.convertSetsToLists': True,
    'yaql.convertTuplesToLists': True,
    'yaql.iterableDicts': True
}

ENGINE_12_OPTIONS = {
    'yaql.limitIterators': constants.ITERATORS_LIMIT,
    'yaql.memoryQuota': constants.EXPRESSION_MEMORY_QUOTA,
    'yaql.convertSetsToLists': True,
    'yaql.convertTuplesToLists': True
}


def _create_engine(runtime_version):
    engine_factory = factory.YaqlFactory()
    engine_factory.insert_operator(
        '.', True, ':', factory.OperatorType.BINARY_LEFT_ASSOCIATIVE, True)
    options = (ENGINE_10_OPTIONS
               if runtime_version <= constants.RUNTIME_VERSION_1_1
               else ENGINE_12_OPTIONS)
    return engine_factory.create(options=options)


@specs.name('#finalize')
def _finalize(obj, context):
    return helpers.evaluate(obj, context)

CONVENTION = conventions.CamelCaseConvention()
ENGINE_10 = _create_engine(constants.RUNTIME_VERSION_1_0)
ENGINE_12 = _create_engine(constants.RUNTIME_VERSION_1_2)
ROOT_CONTEXT_10 = legacy.create_context(
    convention=CONVENTION, finalizer=_finalize)
ROOT_CONTEXT_12 = yaql.create_context(
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
    context = contexts.Context(convention=CONVENTION)
    context.register_function(_finalize)
    return context


@helpers.memoize
def create_context(runtime_version):
    if runtime_version <= constants.RUNTIME_VERSION_1_1:
        context = ROOT_CONTEXT_10.create_child_context()
    else:
        context = ROOT_CONTEXT_12.create_child_context()
    context[constants.CTX_YAQL_ENGINE] = choose_yaql_engine(runtime_version)
    return yaql_functions.register(context, runtime_version)


def choose_yaql_engine(runtime_version):
    return (ENGINE_10 if runtime_version <= constants.RUNTIME_VERSION_1_1
            else ENGINE_12)


def parse(expression, runtime_version):
    return choose_yaql_engine(runtime_version)(expression)


def call_func(__context, __name, *args, **kwargs):
    engine = __context[constants.CTX_YAQL_ENGINE]
    return __context(__name, engine)(
        *args,
        **{CONVENTION.convert_parameter_name(key): value
           for key, value in kwargs.iteritems()})


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
    runtime_version = murano_method.murano_class.package.runtime_version
    engine = choose_yaql_engine(runtime_version)

    @specs.method
    @specs.name(murano_method.name)
    def payload(__context, __sender, *args, **kwargs):
        executor = helpers.get_executor(__context)
        args = tuple(dsl.to_mutable(arg, engine) for arg in args)
        kwargs = dsl.to_mutable(kwargs, engine)
        return helpers.evaluate(murano_method.invoke(
            executor, __sender, args, kwargs, __context, True), __context)

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


def get_class_factory_definition(cls, murano_class):
    runtime_version = murano_class.package.runtime_version
    engine = choose_yaql_engine(runtime_version)

    def payload(__context, __sender, *args, **kwargs):
        assert __sender is None
        args = tuple(dsl.to_mutable(arg, engine) for arg in args)
        kwargs = dsl.to_mutable(kwargs, engine)
        with helpers.contextual(__context):
            return helpers.evaluate(cls(*args, **kwargs), __context)

    if hasattr(cls.__init__, 'im_func'):
        fd = specs.get_function_definition(
            cls.__init__.im_func,
            parameter_type_func=lambda name: _infer_parameter_type(
                name, cls.__init__.im_class.__name__),
            convention=CONVENTION)
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
        names = {p.alias or p.name for p in __fd.parameters.itervalues()}
        for name in kwargs.keys():
            if name not in names:
                del kwargs[name]
    return args, kwargs
