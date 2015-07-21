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
import os.path
import types

from yaql.language import expressions as yaql_expressions
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import helpers


NO_VALUE = utils.create_marker('NO_VALUE')


def name(dsl_name):
    def wrapper(cls):
        cls.__murano_name = dsl_name
        return cls
    return wrapper


class MuranoObjectType(yaqltypes.PythonType):
    def __init__(self, murano_class, nullable=False):
        self.murano_class = murano_class
        super(MuranoObjectType, self).__init__(
            (dsl_types.MuranoObject, MuranoObjectInterface), nullable)

    def check(self, value, context, *args, **kwargs):
        if not super(MuranoObjectType, self).check(
                value, context, *args, **kwargs):
            return False
        if isinstance(value, MuranoObjectInterface):
            value = value.object
        if value is None or isinstance(value, yaql_expressions.Expression):
            return True
        murano_class = self.murano_class
        if isinstance(murano_class, types.StringTypes):
            class_loader = helpers.get_class_loader(context)
            murano_class = class_loader.get_class(self.murano_class)
        return murano_class.is_compatible(value)

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        result = super(MuranoObjectType, self).convert(
            value, sender, context, function_spec, engine, *args, **kwargs)
        if isinstance(result, dsl_types.MuranoObject):
            return MuranoObjectInterface(result, engine)
        return result


class ThisParameterType(yaqltypes.HiddenParameterType, yaqltypes.SmartType):
    def __init__(self):
        super(ThisParameterType, self).__init__(False)

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        this = helpers.get_this(context)
        executor = helpers.get_executor(context)
        return MuranoObjectInterface(this, engine, executor)


class InterfacesParameterType(yaqltypes.HiddenParameterType,
                              yaqltypes.SmartType):
    def __init__(self):
        super(InterfacesParameterType, self).__init__(False)

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        this = helpers.get_this(context)
        return Interfaces(engine, this)


class MuranoTypeName(yaqltypes.LazyParameterType, yaqltypes.PythonType):
    def __init__(self, nullable=False, context=None):
        self._context = context
        super(MuranoTypeName, self).__init__(
            (dsl_types.MuranoClassReference,) + types.StringTypes, nullable)

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        context = self._context or context
        if isinstance(value, yaql_expressions.Expression):
            value = value(utils.NO_VALUE, context, engine)
        value = super(MuranoTypeName, self).convert(
            value, sender, context, function_spec, engine)
        if isinstance(value, types.StringTypes):
            class_loader = helpers.get_class_loader(context)
            murano_type = helpers.get_type(context)
            value = dsl_types.MuranoClassReference(
                class_loader.get_class(
                    murano_type.namespace_resolver.resolve_name(value)))
        return value


class MuranoObjectInterface(dsl_types.MuranoObjectInterface):
    class DataInterface(object):
        def __init__(self, object_interface):
            object.__setattr__(self, '__object_interface', object_interface)

        def __getattr__(self, item):
            oi = getattr(self, '__object_interface')
            return oi[item]

        def __setattr__(self, key, value):
            oi = getattr(self, '__object_interface')
            oi[key] = value

    class CallInterface(object):
        def __init__(self, mpl_object, executor):
            self.__object = mpl_object
            self.__executor = executor

        def __getattr__(self, item):
            executor = self.__executor or helpers.get_executor()

            def func(*args, **kwargs):
                self._insert_instruction()
                return self.__object.type.invoke(
                    item, executor, self.__object, args, kwargs,
                    helpers.get_context())
            return func

        @staticmethod
        def _insert_instruction():
            context = helpers.get_context()
            if context:
                frame = inspect.stack()[2]
                location = dsl_types.ExpressionFilePosition(
                    os.path.abspath(frame[1]), frame[2],
                    -1, frame[2], -1)
                context[constants.CTX_CURRENT_INSTRUCTION] = NativeInstruction(
                    frame[4][0].strip(), location)

    def __init__(self, mpl_object, engine, executor=None):
        self.__object = mpl_object
        self.__executor = executor
        self.__engine = engine

    @property
    def object(self):
        return self.__object

    @property
    def id(self):
        return self.__object.object_id

    @property
    def owner(self):
        return self.__object.owner

    @property
    def type(self):
        return self.__object.type

    def data(self):
        return MuranoObjectInterface.DataInterface(self)

    @property
    def extension(self):
        return self.__object.extension

    def cast(self, murano_class):
        return MuranoObjectInterface(
            self.__object.cast(murano_class), self.__engine, self.__executor)

    def __getitem__(self, item):
        context = helpers.get_context()
        return to_mutable(
            self.__object.get_property(item, context), self.__engine)

    def __setitem__(self, key, value):
        context = helpers.get_context()
        value = helpers.evaluate(value, context)
        self.__object.set_property(key, value, context)

    def __call__(self):
        return MuranoObjectInterface.CallInterface(
            self.object, self.__executor)

    def __repr__(self):
        return '<{0}>'.format(repr(self.object))


class YaqlInterface(object):
    def __init__(self, engine, sender=utils.NO_VALUE):
        self.__engine = engine
        self.__sender = sender

    @property
    def context(self):
        return self.__context

    @property
    def engine(self):
        return self.__engine

    @property
    def sender(self):
        return self.__sender

    def on(self, sender):
        return YaqlInterface(self.engine, sender)

    def __getattr__(self, item):
        def stub(*args, **kwargs):
            context = helpers.get_context()
            args = tuple(helpers.evaluate(arg, context) for arg in args)
            kwargs = dict((key, helpers.evaluate(value, context))
                          for key, value in kwargs.iteritems())
            return to_mutable(
                context(item, self.engine, self.sender)(*args, **kwargs),
                self.engine)
        return stub

    def __call__(self, __expression, *args, **kwargs):
        context = helpers.get_context().create_child_context()
        for i, param in enumerate(args):
            context['$' + str(i + 1)] = helpers.evaluate(param, context)
        for arg_name, arg_value in kwargs.iteritems():
            context['$' + arg_name] = helpers.evaluate(arg_value, context)
        parsed = self.engine(__expression)
        res = parsed.evaluate(context=context)
        return to_mutable(res, self.engine)

    def __getitem__(self, item):
        return helpers.get_context()[item]

    def __setitem__(self, key, value):
        helpers.get_context()[key] = value


class Interfaces(object):
    def __init__(self, engine, mpl_object):
        self.__engine = engine
        self.__object = mpl_object

    def yaql(self, sender=utils.NO_VALUE):
        return YaqlInterface(self.__engine, sender)

    def this(self):
        return self.methods(self.__object)

    def methods(self, mpl_object):
        if mpl_object is None:
            return None
        return MuranoObjectInterface(mpl_object, self.__engine)

    @property
    def environment(self):
        return helpers.get_environment()

    @property
    def caller(self):
        caller_context = helpers.get_caller_context()
        if caller_context is None:
            return None
        caller = helpers.get_this(caller_context)
        if caller is None:
            return None
        return MuranoObjectInterface(caller, self.__engine)

    @property
    def attributes(self):
        executor = helpers.get_executor()
        return executor.attribute_store

    @property
    def class_config(self):
        return self.class_loader.get_class_config(self.__object.type.name)

    @property
    def class_loader(self):
        return helpers.get_class_loader()


class NativeInstruction(object):
    def __init__(self, instruction, location):
        self.instruction = instruction
        self.source_file_position = location

    def __str__(self):
        return self.instruction


def to_mutable(obj, yaql_engine):
    def converter(value, limit_func, engine, rec):
        if isinstance(value, dsl_types.MuranoObject):
            return MuranoObjectInterface(value, engine)
        else:
            return utils.convert_output_data(value, limit_func, engine, rec)

    limiter = lambda it: utils.limit_iterable(it, constants.ITERATORS_LIMIT)
    return converter(obj, limiter, yaql_engine, converter)
