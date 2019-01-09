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

import weakref

from oslo_config import cfg
import yaql
from yaql.language import contexts
from yaql.language import conventions
from yaql.language import factory
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes
from yaql import legacy

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import yaql_functions


CONF = cfg.CONF
ENGINE_10_OPTIONS = {
    'yaql.limitIterators': CONF.murano.dsl_iterators_limit,
    'yaql.memoryQuota': constants.EXPRESSION_MEMORY_QUOTA,
    'yaql.convertSetsToLists': True,
    'yaql.convertTuplesToLists': True,
    'yaql.iterableDicts': True
}

ENGINE_12_OPTIONS = {
    'yaql.limitIterators': CONF.murano.dsl_iterators_limit,
    'yaql.memoryQuota': constants.EXPRESSION_MEMORY_QUOTA,
    'yaql.convertSetsToLists': True,
    'yaql.convertTuplesToLists': True
}


def _add_operators(engine_factory):
    engine_factory.insert_operator(
        '>', True, 'is', factory.OperatorType.BINARY_LEFT_ASSOCIATIVE, False)
    engine_factory.insert_operator(
        None, True, ':', factory.OperatorType.BINARY_LEFT_ASSOCIATIVE, True)
    engine_factory.insert_operator(
        ':', True, ':', factory.OperatorType.PREFIX_UNARY, False)
    engine_factory.operators.insert(0, ())


def _create_engine(runtime_version):
    engine_factory = factory.YaqlFactory()
    _add_operators(engine_factory=engine_factory)
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
    def __init__(self, value_spec, with_check=False):
        def converter(value, receiver, context, *args, **kwargs):
            if isinstance(receiver, dsl_types.MuranoObject):
                this = receiver.real_this
            else:
                this = receiver
            return value_spec.transform(
                value, this, context[constants.CTX_ARGUMENT_OWNER],
                context)

        def checker(value, context, *args, **kwargs):
            return value_spec.check_type(value, context)

        super(ContractedValue, self).__init__(
            True, checker if with_check else None, converter)

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
           for key, value in kwargs.items()})


def _infer_parameter_type(name, class_name):
    if name == 'context':
        return yaqltypes.Context()
    if name == 'this':
        return dsl.ThisParameter()
    if name == 'interfaces':
        return dsl.InterfacesParameter()
    if name == 'yaql_engine':
        return yaqltypes.Engine()

    if name.startswith('__'):
        return _infer_parameter_type(name[2:], class_name)
    if class_name and name.startswith('_{0}__'.format(class_name)):
        return _infer_parameter_type(name[3 + len(class_name):], class_name)


def get_function_definition(func, murano_method, original_name):
    cls = murano_method.declaring_type.extension_class

    def param_type_func(name):
        return None if not cls else _infer_parameter_type(name, cls.__name__)

    body = func
    if (cls is None or helpers.inspect_is_method(cls, original_name) or
            helpers.inspect_is_classmethod(cls, original_name)):
        body = helpers.function(func)
    fd = specs.get_function_definition(
        body, convention=CONVENTION,
        parameter_type_func=param_type_func)
    fd.is_method = True
    fd.is_function = False
    if not cls or helpers.inspect_is_method(cls, original_name):
        fd.set_parameter(
            0,
            dsl.MuranoObjectParameter(murano_method.declaring_type),
            overwrite=True)
    if cls and helpers.inspect_is_classmethod(cls, original_name):
        _remove_first_parameter(fd)
        body = func
    name = getattr(func, '__murano_name', None)
    if name:
        fd.name = name
    fd.insert_parameter(specs.ParameterDefinition(
        '?1', yaqltypes.Context(), 0))
    is_static = cls and (
        helpers.inspect_is_static(cls, original_name) or
        helpers.inspect_is_classmethod(cls, original_name))
    if is_static:
        fd.insert_parameter(specs.ParameterDefinition(
            '?2', yaqltypes.PythonType(object), 1))

    def payload(__context, __self, *args, **kwargs):
        with helpers.contextual(__context):
            __context[constants.CTX_NAMES_SCOPE] = \
                murano_method.declaring_type
            return body(__self.extension, *args, **kwargs)

    def static_payload(__context, __receiver, *args, **kwargs):
        with helpers.contextual(__context):
            __context[constants.CTX_NAMES_SCOPE] = \
                murano_method.declaring_type
            return body(*args, **kwargs)

    if is_static:
        fd.payload = static_payload
    else:
        fd.payload = payload
    fd.meta[constants.META_MURANO_METHOD] = murano_method
    return fd


def _remove_first_parameter(fd):
    first_param = None
    first_param_name = None
    for p_name, p in fd.parameters.items():
        if isinstance(p.value_type, yaqltypes.HiddenParameterType):
            continue
        if p.position is None:
            continue
        if first_param is None or p.position < first_param.position:
            first_param = p
            first_param_name = p_name
    if first_param:
        del fd.parameters[first_param_name]
        for p_name, p in fd.parameters.items():
            if p.position is not None and p.position > first_param.position:
                p.position -= 1


def build_stub_function_definitions(murano_method):
    if isinstance(murano_method.body, specs.FunctionDefinition):
        return _build_native_stub_function_definitions(murano_method)
    else:
        return _build_mpl_stub_function_definitions(murano_method)


def _build_native_stub_function_definitions(murano_method):
    runtime_version = murano_method.declaring_type.package.runtime_version
    engine = choose_yaql_engine(runtime_version)

    @specs.method
    @specs.name(murano_method.name)
    @specs.meta(constants.META_MURANO_METHOD, murano_method)
    @specs.parameter('__receiver', yaqltypes.NotOfType(
        dsl_types.MuranoTypeReference))
    def payload(__context, __receiver, *args, **kwargs):
        args = tuple(dsl.to_mutable(arg, engine) for arg in args)
        kwargs = dsl.to_mutable(kwargs, engine)
        return helpers.evaluate(murano_method.invoke(
            __receiver, args, kwargs, __context, True), __context)

    @specs.method
    @specs.name(murano_method.name)
    @specs.meta(constants.META_MURANO_METHOD, murano_method)
    @specs.parameter('__receiver', yaqltypes.NotOfType(
        dsl_types.MuranoTypeReference))
    def extension_payload(__context, __receiver, *args, **kwargs):
        args = tuple(dsl.to_mutable(arg, engine) for arg in args)
        kwargs = dsl.to_mutable(kwargs, engine)
        return helpers.evaluate(murano_method.invoke(
            murano_method.declaring_type, (__receiver,) + args, kwargs,
            __context, True), __context)

    @specs.method
    @specs.name(murano_method.name)
    @specs.meta(constants.META_MURANO_METHOD, murano_method)
    @specs.parameter('__receiver', dsl_types.MuranoTypeReference)
    def static_payload(__context, __receiver, *args, **kwargs):
        args = tuple(dsl.to_mutable(arg, engine) for arg in args)
        kwargs = dsl.to_mutable(kwargs, engine)
        return helpers.evaluate(murano_method.invoke(
            __receiver, args, kwargs, __context, True), __context)

    if murano_method.usage in dsl_types.MethodUsages.InstanceMethods:
        return specs.get_function_definition(payload), None
    elif murano_method.usage == dsl_types.MethodUsages.Static:
        return (specs.get_function_definition(payload),
                specs.get_function_definition(static_payload))
    elif murano_method.usage == dsl_types.MethodUsages.Extension:
        return (specs.get_function_definition(extension_payload),
                specs.get_function_definition(static_payload))
    else:
        raise ValueError('Unknown method usage ' + murano_method.usage)


def _build_mpl_stub_function_definitions(murano_method):
    if murano_method.usage in dsl_types.MethodUsages.InstanceMethods:
        return _create_instance_mpl_stub(murano_method), None
    elif murano_method.usage == dsl_types.MethodUsages.Static:
        return (_create_instance_mpl_stub(murano_method),
                _create_static_mpl_stub(murano_method))
    elif murano_method.usage == dsl_types.MethodUsages.Extension:
        return (_create_extension_mpl_stub(murano_method),
                _create_static_mpl_stub(murano_method))
    else:
        raise ValueError('Unknown method usage ' + murano_method.usage)


def _create_instance_mpl_stub(murano_method):
    def payload(__context, __receiver, *args, **kwargs):
        return murano_method.invoke(__receiver, args, kwargs, __context, True)
    fd = _create_basic_mpl_stub(murano_method, 1, payload, False)

    receiver_type = dsl.MuranoObjectParameter(
        weakref.proxy(murano_method.declaring_type), decorate=False)
    fd.set_parameter(specs.ParameterDefinition('__receiver', receiver_type, 1))
    return fd


def _create_static_mpl_stub(murano_method):
    def payload(__context, __receiver, *args, **kwargs):
        return murano_method.invoke(__receiver, args, kwargs, __context, True)
    fd = _create_basic_mpl_stub(murano_method, 1, payload, False)

    receiver_type = dsl.MuranoTypeParameter(
        weakref.proxy(murano_method.declaring_type), resolve_strings=False)
    fd.set_parameter(specs.ParameterDefinition('__receiver', receiver_type, 1))
    return fd


def _create_extension_mpl_stub(murano_method):
    def payload(__context, __receiver, *args, **kwargs):
        return murano_method.invoke(
            murano_method.declaring_type, (__receiver,) + args, kwargs,
            __context, True)
    return _create_basic_mpl_stub(murano_method, 0, payload, True)


def _create_basic_mpl_stub(murano_method, reserve_params, payload,
                           check_first_arg):
    fd = specs.FunctionDefinition(
        murano_method.name, payload, is_function=False, is_method=True)

    i = reserve_params + 1
    varargs = False
    kwargs = False
    for name, arg_spec in murano_method.arguments_scheme.items():
        position = i
        if arg_spec.usage == dsl_types.MethodArgumentUsages.VarArgs:
            name = '*'
            varargs = True
        elif arg_spec.usage == dsl_types.MethodArgumentUsages.KwArgs:
            name = '**'
            position = None
            kwargs = True
        p = specs.ParameterDefinition(
            name, ContractedValue(arg_spec, with_check=check_first_arg),
            position=position, default=dsl.NO_VALUE)
        check_first_arg = False
        fd.parameters[name] = p
        i += 1

    if not varargs:
        fd.parameters['*'] = specs.ParameterDefinition(
            '*',
            value_type=yaqltypes.PythonType(object, nullable=True),
            position=i)
    if not kwargs:
        fd.parameters['**'] = specs.ParameterDefinition(
            '**', value_type=yaqltypes.PythonType(object, nullable=True))

    fd.set_parameter(specs.ParameterDefinition(
        '__context', yaqltypes.Context(), 0))

    fd.meta[constants.META_MURANO_METHOD] = murano_method
    return fd


def get_class_factory_definition(cls, murano_class):
    runtime_version = murano_class.package.runtime_version
    engine = choose_yaql_engine(runtime_version)

    def payload(__context, __receiver, *args, **kwargs):
        args = tuple(dsl.to_mutable(arg, engine) for arg in args)
        kwargs = dsl.to_mutable(kwargs, engine)
        with helpers.contextual(__context):
            __context[constants.CTX_NAMES_SCOPE] = murano_class
            result = helpers.evaluate(cls(*args, **kwargs), __context)
            __receiver.object.extension = result

    try:
        fd = specs.get_function_definition(
            helpers.function(cls.__init__),
            parameter_type_func=lambda name: _infer_parameter_type(
                name, cls.__name__),
            convention=CONVENTION)
    except AttributeError:
        # __init__ is a slot wrapper inherited from object or other C type
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
        for p in __fd.parameters.values():
            if p.position is not None:
                position_args += 1
        args = args[:position_args]
    kwargs = kwargs.copy()
    for name in list(kwargs.keys()):
        if not utils.is_keyword(name):
            del kwargs[name]
    if '**' not in __fd.parameters:
        names = {p.alias or p.name for p in __fd.parameters.values()}
        for name in list(kwargs.keys()):
            if name not in names:
                del kwargs[name]
    return args, kwargs
