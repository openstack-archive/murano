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

from muranoapi.engine import consts
from muranoapi.engine import helpers
from muranoapi.engine import objects
from muranoapi.engine import typespec


class MuranoClass(object):
    def __init__(self, class_loader, namespace_resolver, name, parents=None):
        self._class_loader = class_loader
        self._namespace_resolver = namespace_resolver
        self._name = namespace_resolver.resolve_name(name)
        self._properties = {}
        if self._name == consts.ROOT_CLASS:
            self._parents = []
        else:
            self._parents = parents if parents is not None else [
                class_loader.get_class(consts.ROOT_CLASS)]
        self.object_class = type(
            'mc' + helpers.generate_id(),
            tuple([p.object_class for p in self._parents]) or (
                objects.MuranoObject,),
            {})

    @property
    def name(self):
        return self._name

    @property
    def namespace_resolver(self):
        return self._namespace_resolver

    @property
    def parents(self):
        return self._parents

    @property
    def properties(self):
        return self._properties.keys()

    def add_property(self, name, property_typespec):
        if not isinstance(property_typespec, typespec.PropertySpec):
            raise TypeError('property_typespec')
        self._properties[name] = property_typespec

    def get_property(self, name):
        return self._properties[name]

    def find_property(self, name):
        types = collections.deque([self])
        while len(types) > 0:
            mc = types.popleft()
            if name in mc.properties:
                return mc.get_property(name)
            types.extend(mc.parents)
        return None

    def is_compatible(self, obj):
        if isinstance(obj, objects.MuranoObject):
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
