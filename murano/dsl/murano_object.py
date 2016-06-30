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

import weakref

import six

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import yaql_integration


class MuranoObject(dsl_types.MuranoObject):
    def __init__(self, murano_class, owner, object_store, executor,
                 object_id=None, name=None, known_classes=None, this=None):
        if known_classes is None:
            known_classes = {}
        self.__owner = owner.real_this if owner else None
        self.__object_id = object_id or helpers.generate_id()
        self.__type = murano_class
        self.__properties = {}
        self.__parents = {}
        self.__this = this
        self.__name = name
        self.__extension = None
        self.__object_store = \
            None if object_store is None else weakref.ref(object_store)
        self.__executor = weakref.ref(executor)
        self.__config = murano_class.package.get_class_config(
            murano_class.name)
        if not isinstance(self.__config, dict):
            self.__config = {}
        known_classes[murano_class.name] = self
        for parent_class in murano_class.parents(self.real_this.type):
            name = parent_class.name
            if name not in known_classes:
                obj = parent_class.new(
                    owner, object_store, executor, object_id=self.__object_id,
                    known_classes=known_classes, this=self.real_this).object

                self.__parents[name] = known_classes[name] = obj
            else:
                self.__parents[name] = known_classes[name]
        self.__initialized = False

    @property
    def extension(self):
        return self.__extension

    @property
    def name(self):
        return self.real_this.__name

    @extension.setter
    def extension(self, value):
        self.__extension = value

    @property
    def object_store(self):
        return None if self.__object_store is None else self.__object_store()

    @property
    def executor(self):
        return self.__executor()

    def initialize(self, context, object_store, params):
        if self.__initialized:
            return
        for property_name in self.__type.properties:
            spec = self.__type.properties[property_name]
            if spec.usage == dsl_types.PropertyUsages.Config:
                if property_name in self.__config:
                    property_value = self.__config[property_name]
                else:
                    property_value = dsl.NO_VALUE
                self.set_property(property_name, property_value)

        init = self.type.methods.get('.init')
        used_names = set()
        names = set(self.__type.properties)
        if init:
            names.update(six.iterkeys(init.arguments_scheme))
        last_errors = len(names)
        init_args = {}
        while True:
            errors = 0
            for property_name in names:
                if init and property_name in init.arguments_scheme:
                    spec = init.arguments_scheme[property_name]
                    is_init_arg = True
                else:
                    spec = self.__type.properties[property_name]
                    is_init_arg = False

                if property_name in used_names:
                    continue
                if spec.usage in (dsl_types.PropertyUsages.Config,
                                  dsl_types.PropertyUsages.Static):
                    used_names.add(property_name)
                    continue
                if spec.usage == dsl_types.PropertyUsages.Runtime:
                    if not spec.has_default:
                        used_names.add(property_name)
                        continue
                    property_value = dsl.NO_VALUE
                else:
                    property_value = params.get(property_name, dsl.NO_VALUE)
                try:
                    if is_init_arg:
                        init_args[property_name] = property_value
                    else:
                        self.set_property(
                            property_name, property_value, context)
                    used_names.add(property_name)
                except exceptions.UninitializedPropertyAccessError:
                    errors += 1
                except exceptions.ContractViolationException:
                    if spec.usage != dsl_types.PropertyUsages.Runtime:
                        raise
            if not errors:
                break
            if errors >= last_errors:
                raise exceptions.CircularExpressionDependenciesError()
            last_errors = errors

        executor = helpers.get_executor(context)
        if ((object_store is None or not object_store.initializing) and
                self.__extension is None):
            method = self.type.methods.get('__init__')
            if method:
                filtered_params = yaql_integration.filter_parameters(
                    method.body, **params)

                self.__extension = method.invoke(
                    executor, self, filtered_params[0],
                    filtered_params[1], context)

        for parent in self.__parents.values():
            parent.initialize(context, object_store, params)

        if (object_store is None or not object_store.initializing) and init:
            context[constants.CTX_ARGUMENT_OWNER] = self.real_this
            init.invoke(executor, self.real_this, (), init_args, context)
            self.__initialized = True

        if object_store is not None and not object_store.initializing:
            object_store.put(self.real_this)

    @property
    def object_id(self):
        return self.__object_id

    @property
    def type(self):
        return self.__type

    @property
    def owner(self):
        return self.__owner

    @property
    def real_this(self):
        return self.__this or self

    def get_property(self, name, context=None):
        start_type, derived = self.__type, False
        caller_class = None if not context else helpers.get_type(context)
        if caller_class is not None and caller_class.is_compatible(self):
            start_type, derived = caller_class, True
        if name in start_type.properties:
            spec = start_type.properties[name]
            if spec.usage == dsl_types.PropertyUsages.Static:
                return spec.declaring_type.get_property(name, context)
            else:
                return self.cast(start_type)._get_property_value(name)
        else:
            try:
                spec = start_type.find_single_property(name)
                if spec.usage == dsl_types.PropertyUsages.Static:
                    return spec.declaring_type.get_property(name, context)
                else:
                    return self.cast(spec.declaring_type).__properties[name]
            except exceptions.NoPropertyFound:
                if derived:
                    return self.cast(caller_class)._get_property_value(name)
                else:
                    raise exceptions.PropertyReadError(name, start_type)

    def _get_property_value(self, name):
        try:
            return self.__properties[name]
        except KeyError:
            raise exceptions.UninitializedPropertyAccessError(
                name, self.__type)

    def set_property(self, name, value, context=None):
        start_type, derived = self.__type, False
        caller_class = None if not context else helpers.get_type(context)
        if caller_class is not None and caller_class.is_compatible(self):
            start_type, derived = caller_class, True
        declared_properties = start_type.find_properties(
            lambda p: p.name == name)
        if context is None:
            context = self.executor.create_object_context(self)
        if len(declared_properties) > 0:
            declared_properties = self.type.find_properties(
                lambda p: p.name == name)
            values_to_assign = []
            classes_for_static_properties = []
            for spec in declared_properties:
                if (caller_class is not None and not
                        helpers.are_property_modifications_allowed(context) and
                        (spec.usage not in dsl_types.PropertyUsages.Writable or
                            not derived)):
                    raise exceptions.NoWriteAccessError(name)

                if spec.usage == dsl_types.PropertyUsages.Static:
                    classes_for_static_properties.append(spec.declaring_type)
                else:
                    default = self.__config.get(name, spec.default)
                    # default = helpers.evaluate(default, context)

                    obj = self.cast(spec.declaring_type)
                    values_to_assign.append((obj, spec.transform(
                        value, self.real_this,
                        self.real_this, context, default=default)))
            for obj, value in values_to_assign:
                obj.__properties[name] = value
            for cls in classes_for_static_properties:
                cls.set_property(name, value, context)
        elif derived:
            obj = self.cast(caller_class)
            obj.__properties[name] = value
        else:
            raise exceptions.PropertyWriteError(name, start_type)

    def cast(self, cls):
        for p in helpers.traverse(self, lambda t: t.__parents.values()):
            if p.type is cls:
                return p
        raise TypeError('Cannot cast {0} to {1}'.format(self.type, cls))

    def __repr__(self):
        return '<{0}/{1} {2} ({3})>'.format(
            self.type.name, self.type.version, self.object_id, id(self))

    def to_dictionary(self, include_hidden=False):
        result = {}
        for parent in self.__parents.values():
            result.update(parent.to_dictionary(include_hidden))
        result.update({'?': {
            'type': self.type.name,
            'id': self.object_id,
            'name': self.name,
            'classVersion': str(self.type.version),
            'package': self.type.package.name
        }})
        if include_hidden:
            result.update(self.__properties)
        else:
            for property_name in self.type.properties:
                if property_name in self.__properties:
                    spec = self.type.properties[property_name]
                    if spec.usage != dsl_types.PropertyUsages.Runtime:
                        result[property_name] = self.__properties[
                            property_name]
        return result
