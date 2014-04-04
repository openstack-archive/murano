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

import collections
import inspect

import muranoapi.dsl.helpers as helpers
import muranoapi.dsl.murano_method as murano_method
import muranoapi.dsl.murano_object as murano_object
import muranoapi.dsl.typespec as typespec


def classname(name):
    def wrapper(cls):
        cls._murano_class_name = name
        return cls
    return wrapper


class MuranoClass(object):
    def __init__(self, class_loader, namespace_resolver, name, package,
                 parents=None):
        self._package = package
        self._class_loader = class_loader
        self._methods = {}
        self._namespace_resolver = namespace_resolver
        self._name = namespace_resolver.resolve_name(name)
        self._properties = {}
        if self._name == 'io.murano.Object':
            self._parents = []
        else:
            self._parents = parents or [
                class_loader.get_class('io.murano.Object')]

        class_name = 'mc' + helpers.generate_id()
        parents_class = [p.object_class for p in self._parents]
        bases = tuple(parents_class) or (murano_object.MuranoObject,)

        self.object_class = type(class_name, bases, {})

    @property
    def name(self):
        return self._name

    @property
    def package(self):
        return self._package

    @property
    def namespace_resolver(self):
        return self._namespace_resolver

    @property
    def parents(self):
        return self._parents

    @property
    def methods(self):
        return self._methods

    def get_method(self, name):
        return self._methods.get(name)

    def add_method(self, name, payload):
        method = murano_method.MuranoMethod(self._namespace_resolver,
                                            self, name, payload)
        self._methods[name] = method
        return method

    @property
    def properties(self):
        return self._properties.keys()

    def add_property(self, name, property_typespec):
        if not isinstance(property_typespec, typespec.PropertySpec):
            raise TypeError('property_typespec')
        self._properties[name] = property_typespec

    def get_property(self, name):
        return self._properties[name]

    def find_method(self, name):
        #resolved_name = self._namespace_resolver.resolve_name(name, self.name)
        if name in self._methods:
            return [(self, name)]
        if not self._parents:
            return []
        return list(set(reduce(
            lambda x, y: x + y,
            [p.find_method(name) for p in self._parents])))

    def find_property(self, name):
        types = collections.deque([self])
        while len(types) > 0:
            mc = types.popleft()
            if name in mc.properties:
                return mc.get_property(name)
            types.extend(mc.parents)
        return None

    def invoke(self, name, executor, this, parameters):
        args = executor.to_yaql_args(parameters)
        return executor.invoke_method(name, this, None, self, *args)

    def is_compatible(self, obj):
        if isinstance(obj, murano_object.MuranoObject):
            return self.is_compatible(obj.type)
        if obj is self:
            return True
        for parent in obj.parents:
            if self.is_compatible(parent):
                return True
        return False

    def new(self, parent, object_store, context, parameters=None,
            object_id=None, **kwargs):

        obj = self.object_class(self, parent, object_store, context,
                                object_id=object_id, **kwargs)
        if parameters is not None:
            argspec = inspect.getargspec(obj.initialize).args
            if '_context' in argspec:
                parameters['_context'] = context
            if '_parent' in argspec:
                parameters['_parent'] = parent
            obj.initialize(**parameters)
        return obj

    def __str__(self):
        return 'MuranoClass({0})'.format(self.name)
