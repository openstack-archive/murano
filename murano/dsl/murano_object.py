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

import yaml
import yaql.context

import murano.dsl.exceptions as exceptions
import murano.dsl.helpers
import murano.dsl.type_scheme as type_scheme
import murano.dsl.typespec as typespec


class MuranoObject(object):
    def __init__(self, murano_class, owner, object_store, context,
                 object_id=None, known_classes=None, defaults=None, this=None):

        if known_classes is None:
            known_classes = {}
        self.__owner = owner
        self.__object_id = object_id or murano.dsl.helpers.generate_id()
        self.__type = murano_class
        self.__properties = {}
        self.__object_store = object_store
        self.__parents = {}
        self.__context = context
        self.__defaults = defaults or {}
        self.__this = this
        self.__config = object_store.class_loader.get_class_config(
            murano_class.name)
        if not isinstance(self.__config, dict):
            self.__config = {}
        known_classes[murano_class.name] = self
        for parent_class in murano_class.parents:
            name = parent_class.name
            if name not in known_classes:
                obj = parent_class.new(owner, object_store, context,
                                       None, object_id=self.__object_id,
                                       known_classes=known_classes,
                                       defaults=defaults, this=self.real_this)

                self.__parents[name] = known_classes[name] = obj
            else:
                self.__parents[name] = known_classes[name]

    def initialize(self, **kwargs):
        used_names = set()
        for property_name in self.__type.properties:
            spec = self.__type.get_property(property_name)
            if spec.usage == typespec.PropertyUsages.Config:
                if property_name in self.__config:
                    property_value = self.__config[property_name]
                else:
                    property_value = type_scheme.NoValue
                self.set_property(property_name, property_value)

        for i in xrange(2):
            for property_name in self.__type.properties:
                spec = self.__type.get_property(property_name)
                if spec.usage == typespec.PropertyUsages.Config:
                    continue
                needs_evaluation = murano.dsl.helpers.needs_evaluation
                if i == 0 and needs_evaluation(spec.default) or i == 1\
                        and property_name in used_names:
                    continue
                used_names.add(property_name)
                if spec.usage == typespec.PropertyUsages.Runtime:
                    if not spec.has_default:
                        continue
                    property_value = type_scheme.NoValue
                else:
                    property_value = kwargs.get(property_name,
                                                type_scheme.NoValue)
                try:
                    self.set_property(property_name, property_value)
                except exceptions.ContractViolationException:
                    if spec.usage != typespec.PropertyUsages.Runtime:
                        raise

        for parent in self.__parents.values():
            parent.initialize(**kwargs)
        self.__initialized = True

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

    def __getattr__(self, item):
        if item.startswith('__'):
            raise AttributeError('Access to internal attributes is '
                                 'restricted')
        return self.get_property(item)

    def get_property(self, name, caller_class=None):
        start_type, derived = self.__type, False
        if caller_class is not None and caller_class.is_compatible(self):
            start_type, derived = caller_class, True
        if name in start_type.properties:
            return self.cast(start_type)._get_property_value(name)
        else:
            declared_properties = start_type.find_property(name)
            if len(declared_properties) == 1:
                return self.cast(declared_properties[0]).__properties[name]
            elif len(declared_properties) > 1:
                raise exceptions.AmbiguousPropertyNameError(name)
            elif derived:
                return self.cast(caller_class)._get_property_value(name)
            else:
                raise exceptions.PropertyReadError(name, start_type)

    def _get_property_value(self, name):
        try:
            return self.__properties[name]
        except KeyError:
            raise exceptions.UninitializedPropertyAccessError(
                name, self.__type)

    def set_property(self, name, value, caller_class=None):
        start_type, derived = self.__type, False
        if caller_class is not None and caller_class.is_compatible(self):
            start_type, derived = caller_class, True
        declared_properties = start_type.find_property(name)
        if len(declared_properties) > 0:
            declared_properties = self.type.find_property(name)
            values_to_assign = []
            for mc in declared_properties:
                spec = mc.get_property(name)
                if caller_class is not None:
                    if spec.usage not in typespec.PropertyUsages.Writable \
                            or not derived:
                        raise exceptions.NoWriteAccessError(name)

                default = self.__config.get(name, spec.default)
                default = self.__defaults.get(name, default)
                child_context = yaql.context.Context(
                    parent_context=self.__context)
                child_context.set_data(self)
                default = murano.dsl.helpers.evaluate(
                    default, child_context, 1)

                obj = self.cast(mc)
                values_to_assign.append((obj, spec.validate(
                    value, self, self,
                    self.__context, self.__object_store, default)))
            for obj, value in values_to_assign:
                obj.__properties[name] = value
        elif derived:
                obj = self.cast(caller_class)
                obj.__properties[name] = value
        else:
            raise exceptions.PropertyWriteError(name, start_type)

    def cast(self, type):
        if self.type is type:
            return self
        for parent in self.__parents.values():
            try:
                return parent.cast(type)
            except TypeError:
                continue
        raise TypeError('Cannot cast')

    def __repr__(self):
        return yaml.safe_dump(murano.dsl.helpers.serialize(self))

    def to_dictionary(self, include_hidden=False):
        result = {}
        for parent in self.__parents.values():
            result.update(parent.to_dictionary(include_hidden))
        result.update({'?': {'type': self.type.name, 'id': self.object_id}})
        if include_hidden:
            result.update(self.__properties)
        else:
            for property_name in self.type.properties:
                if property_name in self.__properties:
                    spec = self.type.get_property(property_name)
                    if spec.usage != typespec.PropertyUsages.Runtime:
                        result[property_name] = \
                            self.__properties[property_name]
        return result
