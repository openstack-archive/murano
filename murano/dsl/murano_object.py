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

import types

import yaml
import yaql.context

import murano.dsl.exceptions as exceptions
import murano.dsl.helpers
import murano.dsl.type_scheme as type_scheme
import murano.dsl.typespec as typespec


class MuranoObject(object):
    def __init__(self, murano_class, parent_obj, object_store, context,
                 object_id=None, known_classes=None, defaults=None, this=None):

        if known_classes is None:
            known_classes = {}
        self.__parent_obj = parent_obj
        self.__object_id = object_id or murano.dsl.helpers.generate_id()
        self.__type = murano_class
        self.__properties = {}
        self.__object_store = object_store
        self.__parents = {}
        self.__context = context
        self.__defaults = defaults or {}
        self.__this = this
        known_classes[murano_class.name] = self
        for parent_class in murano_class.parents:
            name = parent_class.name
            if name not in known_classes:
                obj = parent_class.new(parent_obj, object_store, context,
                                       None, object_id=self.__object_id,
                                       known_classes=known_classes,
                                       defaults=defaults, this=self.real_this)

                self.__parents[name] = known_classes[name] = obj
            else:
                self.__parents[name] = known_classes[name]

    def initialize(self, **kwargs):
        used_names = set()
        for i in xrange(2):
            for property_name in self.__type.properties:
                spec = self.__type.get_property(property_name)
                needs_evaluation = murano.dsl.helpers.needs_evaluation
                if i == 0 and needs_evaluation(spec.default) or i == 1\
                        and property_name in used_names:
                    continue
                used_names.add(property_name)
                property_value = kwargs.get(property_name, type_scheme.NoValue)
                self.set_property(property_name, property_value)
        for parent in self.__parents.values():
            parent.initialize(**kwargs)

    @property
    def object_id(self):
        return self.__object_id

    @property
    def type(self):
        return self.__type

    @property
    def parent(self):
        return self.__parent_obj

    @property
    def real_this(self):
        return self.__this or self

    def __getattr__(self, item):
        if item.startswith('__'):
            raise AttributeError('Access to internal attributes is '
                                 'restricted')
        return self.get_property(item)

    def get_property(self, item, caller_class=None):
        try:
            return self.__get_property(item, caller_class)
        except AttributeError:
            if not caller_class:
                raise AttributeError(item)
            try:
                obj = self.cast(caller_class)
                return obj.__properties[item]
            except KeyError:
                raise AttributeError(item)
            except TypeError:
                raise AttributeError(item)

    def __get_property(self, item, caller_class=None):
        if item in self.__properties and item in self.type.properties:
            return self.__properties[item]
        i = 0
        result = None
        for parent in self.__parents.values():
            try:
                result = parent.__get_property(item, caller_class)
                i += 1
                if i > 1:
                    raise LookupError()
            except AttributeError:
                continue
        if not i:
            raise AttributeError()
        return result

    def set_property(self, key, value, caller_class=None):
        try:
            self.__set_property(key, value, caller_class)
        except AttributeError as e:
            if not caller_class:
                raise e
            try:
                obj = self.cast(caller_class)
                obj.__properties[key] = value
            except TypeError:
                raise AttributeError(key)

    def __set_property(self, key, value, caller_class=None):
        if key in self.__type.properties:
            spec = self.__type.get_property(key)
            if caller_class is not None \
                    and (spec.usage not in typespec.PropertyUsages.Writable
                         or not caller_class.is_compatible(self)):
                raise exceptions.NoWriteAccess(key)

            default = self.__defaults.get(key, spec.default)
            child_context = yaql.context.Context(parent_context=self.__context)
            child_context.set_data(self)
            default = murano.dsl.helpers.evaluate(default, child_context, 1)

            self.__properties[key] = spec.validate(
                value, self, self.__context, self.__object_store, default)
        else:
            for parent in self.__parents.values():
                try:
                    parent.__set_property(key, value, caller_class)
                    return
                except AttributeError:
                    continue
            raise AttributeError(key)

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

    def __merge_default(self, src, defaults):
        if src is None:
            return
        if type(src) != type(defaults):
            raise ValueError()
        if isinstance(defaults, types.DictionaryType):
            for key, value in defaults.iteritems():
                src_value = src.get(key)
                if src_value is None:
                    continue
