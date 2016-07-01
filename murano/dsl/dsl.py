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

import six
from yaql.language import expressions as yaql_expressions
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes
from yaql import yaql_interface

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import helpers


NO_VALUE = utils.create_marker('NO_VALUE')


def name(dsl_name):
    def wrapper(cls):
        cls.__murano_name = dsl_name
        return cls
    return wrapper


class MuranoObjectParameter(yaqltypes.PythonType):
    def __init__(self, murano_class=None, nullable=False, version_spec=None,
                 decorate=True):
        self.murano_class = murano_class
        self.version_spec = version_spec
        self.decorate = decorate
        super(MuranoObjectParameter, self).__init__(
            (dsl_types.MuranoObject, MuranoObjectInterface), nullable)

    def check(self, value, context, *args, **kwargs):
        if not super(MuranoObjectParameter, self).check(
                value, context, *args, **kwargs):
            return False
        if value is None or isinstance(value, yaql_expressions.Expression):
            return True
        if isinstance(value, MuranoObjectInterface):
            value = value.object
        if not isinstance(value, dsl_types.MuranoObject):
            return False
        if self.murano_class:
            murano_class = self.murano_class
            if isinstance(murano_class, six.string_types):
                return helpers.is_instance_of(
                    value, murano_class,
                    self.version_spec or helpers.get_type(context))
            else:
                return murano_class.is_compatible(value)
        else:
            return True

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        result = super(MuranoObjectParameter, self).convert(
            value, sender, context, function_spec, engine, *args, **kwargs)
        if result is None:
            return None
        if self.decorate:
            if isinstance(result, MuranoObjectInterface):
                return result
            return MuranoObjectInterface(result)
        else:
            if isinstance(result, dsl_types.MuranoObject):
                return result
            return result.object


class ThisParameter(yaqltypes.HiddenParameterType, yaqltypes.SmartType):
    def __init__(self):
        super(ThisParameter, self).__init__(False)

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        this = helpers.get_this(context)
        if isinstance(this, dsl_types.MuranoObject):
            executor = helpers.get_executor(context)
            return MuranoObjectInterface(this, executor)
        return this


class InterfacesParameter(yaqltypes.HiddenParameterType,
                          yaqltypes.SmartType):
    def __init__(self):
        super(InterfacesParameter, self).__init__(False)

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        this = helpers.get_this(context)
        return Interfaces(this)


class MuranoTypeParameter(yaqltypes.PythonType):
    def __init__(self, base_type=None, nullable=False, context=None,
                 resolve_strings=True):
        self._context = context
        self._base_type = base_type
        self._resolve_strings = resolve_strings
        super(MuranoTypeParameter, self).__init__(
            (dsl_types.MuranoTypeReference,
             six.string_types), nullable)

    def check(self, value, context, *args, **kwargs):
        if not super(MuranoTypeParameter, self).check(
                value, context, *args, **kwargs):
            return False
        if isinstance(value, six.string_types):
            if not self._resolve_strings:
                return False
            value = helpers.get_class(value, context).get_reference()
        if isinstance(value, dsl_types.MuranoTypeReference):
            if not self._base_type:
                return True
            return self._base_type.is_compatible(value)
        return True

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        context = self._context or context
        if isinstance(value, yaql_expressions.Expression):
            value = value(utils.NO_VALUE, context, engine)
        value = super(MuranoTypeParameter, self).convert(
            value, sender, context, function_spec, engine)
        if isinstance(value, six.string_types):
            value = helpers.get_class(value, context).get_reference()
        if self._base_type and not self._base_type.is_compatible(value):
            raise ValueError('Value must be subtype of {0}'.format(
                self._base_type.name
            ))
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

    def __init__(self, mpl_object, executor=None):
        self.__object = mpl_object
        self.__executor = executor

    @property
    def object(self):
        return self.__object

    @property
    def id(self):
        return self.__object.object_id

    @property
    def owner(self):
        owner = self.__object.owner
        if owner is None:
            return None
        return MuranoObjectInterface(owner, self.__executor)

    def find_owner(self, type, optional=False):
        if isinstance(type, six.string_types):
            type = helpers.get_class(type)
        elif isinstance(type, dsl_types.MuranoTypeReference):
            type = type.type
        p = self.__object.owner
        while p is not None:
            if type.is_compatible(p):
                return MuranoObjectInterface(p, self.__executor)
            p = p.owner
        if not optional:
            raise ValueError('Object is not owned by any instance of type '
                             '{0}'.format(type.name))
        return None

    @property
    def type(self):
        return self.__object.type

    @property
    def package(self):
        return self.type.package

    @property
    def properties(self):
        return MuranoObjectInterface.DataInterface(self)

    @property
    def name(self):
        return self.object.name

    @property
    def extension(self):
        return self.__object.extension

    def cast(self, murano_class, version_spec=None):
        return MuranoObjectInterface(
            helpers.cast(
                self.__object, murano_class,
                version_spec or helpers.get_type()),
            self.__executor)

    def is_instance_of(self, murano_class, version_spec=None):
        return helpers.is_instance_of(
            self.__object, murano_class,
            version_spec or helpers.get_type())

    def ancestors(self):
        return self.type.ancestors()

    def __getitem__(self, item):
        context = helpers.get_context()
        return to_mutable(
            self.__object.get_property(item, context),
            helpers.get_yaql_engine(context))

    def __setitem__(self, key, value):
        context = helpers.get_context()
        value = helpers.evaluate(value, context)
        self.__object.set_property(key, value, context)

    def __call__(self):
        return MuranoObjectInterface.CallInterface(
            self.object, self.__executor)

    def __repr__(self):
        return '<{0}>'.format(repr(self.object))

    def __eq__(self, other):
        if isinstance(other, MuranoObjectInterface):
            return self.object == other.object
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.object)


class Interfaces(object):
    def __init__(self, mpl_object):
        self.__object = mpl_object

    def yaql(self, receiver=utils.NO_VALUE):
        return yaql_interface.YaqlInterface(
            helpers.get_context(), helpers.get_yaql_engine(), receiver)

    def this(self):
        return self.methods(self.__object)

    def methods(self, mpl_object):
        if mpl_object is None:
            return None
        return MuranoObjectInterface(mpl_object)

    @property
    def execution_session(self):
        return helpers.get_execution_session()

    @property
    def caller(self):
        caller_context = helpers.get_caller_context()
        if caller_context is None:
            return None
        caller = helpers.get_this(caller_context)
        if caller is None:
            return None
        return MuranoObjectInterface(caller)

    @property
    def attributes(self):
        executor = helpers.get_executor()
        return executor.attribute_store

    @property
    def class_config(self):
        return self.__object.type.package.get_class_config(
            self.__object.type.name)

    @property
    def package_loader(self):
        return helpers.get_package_loader()


class NativeInstruction(object):
    def __init__(self, instruction, location):
        self.instruction = instruction
        self.source_file_position = location

    def __str__(self):
        return self.instruction


def to_mutable(obj, yaql_engine=None):
    if yaql_engine is None:
        yaql_engine = helpers.get_yaql_engine()

    def converter(value, limit_func, engine, rec):
        if isinstance(value, dsl_types.MuranoObject):
            return MuranoObjectInterface(value)
        else:
            return utils.convert_output_data(value, limit_func, engine, rec)

    limiter = lambda it: utils.limit_iterable(it, constants.ITERATORS_LIMIT)
    return converter(obj, limiter, yaql_engine, converter)


def meta(type_name, value):
    def wrapper(func):
        fd = specs.get_function_definition(func)
        mpl_meta = fd.meta.get(constants.META_MPL_META, [])
        mpl_meta.append({type_name: value})
        specs.meta(type_name, mpl_meta)(func)
    return wrapper
