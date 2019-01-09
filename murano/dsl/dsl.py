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

import eventlet
from oslo_config import cfg
import six
from yaql.language import expressions as yaql_expressions
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes
from yaql import yaql_interface

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import helpers


CONF = cfg.CONF
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
        if self.decorate:
            return MuranoObjectInterface.create(result)
        else:
            if isinstance(result, dsl_types.MuranoObject):
                return result
            return None if result is None else result.object


class ThisParameter(yaqltypes.HiddenParameterType, yaqltypes.SmartType):
    def __init__(self):
        super(ThisParameter, self).__init__(False)

    def convert(self, value, sender, context, function_spec, engine,
                *args, **kwargs):
        return get_this(context)


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
                 resolve_strings=True, lazy=False):
        self._context = context
        self._base_type = base_type
        self._resolve_strings = resolve_strings
        self._lazy = lazy
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

        def implementation(ctx=None):
            value2 = value
            if ctx is None:
                ctx = self._context or context
            if isinstance(value2, yaql_expressions.Expression):
                value2 = value2(utils.NO_VALUE, ctx, engine)
            value2 = super(MuranoTypeParameter, self).convert(
                value2, sender, ctx, function_spec, engine)
            if isinstance(value2, six.string_types):
                value2 = helpers.get_class(value2, ctx).get_reference()
            if self._base_type and not self._base_type.is_compatible(value):
                raise ValueError('Value must be subtype of {0}'.format(
                    self._base_type.name
                ))
            return value2

        if self._lazy:
            return implementation
        return implementation()


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
        def __init__(self, object_interface):
            self.__object_interface = object_interface

        def __getattr__(self, item):
            def func(*args, **kwargs):
                self._insert_instruction()
                with helpers.with_object_store(
                        self.__object_interface._object_store):
                    context = helpers.get_context()
                    obj = self.__object_interface.object
                    return to_mutable(obj.type.invoke(
                        item, obj, args, kwargs,
                        context), helpers.get_yaql_engine(context))
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

    def __init__(self, mpl_object):
        self._object = mpl_object
        self._object_store = helpers.get_object_store()

    @staticmethod
    def create(mpl_object):
        if mpl_object is None or isinstance(mpl_object, MuranoObjectInterface):
            return mpl_object
        return MuranoObjectInterface(mpl_object)

    @property
    def object(self):
        return self._object

    @property
    def id(self):
        return self.object.object_id

    @property
    def owner(self):
        owner = self.object.owner
        return MuranoObjectInterface.create(owner)

    def find_owner(self, type, optional=False):
        if isinstance(type, six.string_types):
            type = helpers.get_class(type)
        elif isinstance(type, dsl_types.MuranoTypeReference):
            type = type.type
        owner = helpers.find_object_owner(
            self.object, lambda t: type.is_compatible(t))
        if owner:
            return MuranoObjectInterface(owner)
        if not optional:
            raise ValueError('Object is not owned by any instance of type '
                             '{0}'.format(type.name))
        return None

    @property
    def type(self):
        return self.object.type

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
        return self.object.extension

    def cast(self, murano_class, version_spec=None):
        return MuranoObjectInterface.create(
            helpers.cast(
                self.object, murano_class,
                version_spec or helpers.get_type()))

    def is_instance_of(self, murano_class, version_spec=None):
        return helpers.is_instance_of(
            self.object, murano_class,
            version_spec or helpers.get_type())

    def ancestors(self):
        return self.type.ancestors()

    def __getitem__(self, item):
        context = helpers.get_context()
        return to_mutable(
            self.object.get_property(item, context),
            helpers.get_yaql_engine(context))

    def __setitem__(self, key, value):
        context = helpers.get_context()
        value = helpers.evaluate(value, context)
        self.object.set_property(key, value, context)

    def __call__(self):
        return MuranoObjectInterface.CallInterface(self)

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
        return MuranoObjectInterface.create(mpl_object)

    @property
    def execution_session(self):
        return helpers.get_execution_session()

    @property
    def caller(self):
        caller_context = helpers.get_caller_context()
        if caller_context is None:
            return None
        return get_this(caller_context)

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
            return MuranoObjectInterface.create(value)
        else:
            return utils.convert_output_data(value, limit_func, engine, rec)

    def limiter(it):
        return utils.limit_iterable(it, CONF.murano.dsl_iterators_limit)

    return converter(obj, limiter, yaql_engine, converter)


def meta(type_name, value):
    def wrapper(func):
        fd = specs.get_function_definition(func)
        mpl_meta = fd.meta.get(constants.META_MPL_META, [])
        mpl_meta.append({type_name: value})
        specs.meta(type_name, mpl_meta)(func)
    return wrapper


def get_this(context=None):
    this = helpers.get_this(context)
    return MuranoObjectInterface.create(this)


def get_execution_session():
    return helpers.get_execution_session()


def spawn(func, *args, **kwargs):
    context = helpers.get_context()
    object_store = helpers.get_object_store()

    def wrapper():
        with helpers.with_object_store(object_store):
            with helpers.contextual(context):
                return func(*args, **kwargs)

    return eventlet.spawn(wrapper)


def new(properties, owner=None, type=None):
    context = helpers.get_context()
    return helpers.get_object_store().load(
        properties, owner, type or get_this(context).type, context=context)
