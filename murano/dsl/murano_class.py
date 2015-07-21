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

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import murano_method
from murano.dsl import murano_object
from murano.dsl import typespec
from murano.dsl import yaql_integration


class GeneratedNativeTypeMetaClass(type):
    def __str__(cls):
        return cls.__name__


class MuranoClass(dsl_types.MuranoClass):
    def __init__(self, class_loader, namespace_resolver, name, package,
                 parents=None):
        self._package = package
        self._class_loader = class_loader
        self._methods = {}
        self._namespace_resolver = namespace_resolver
        self._name = namespace_resolver.resolve_name(name)
        self._properties = {}
        self._config = {}
        if self._name == 'io.murano.Object':
            self._parents = []
        else:
            self._parents = parents or [
                class_loader.get_class('io.murano.Object')]
        self._unique_methods = None

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

    def extend_with_class(self, cls):
        ctor = yaql_integration.get_class_factory_definition(cls)
        self.add_method('__init__', ctor)

    @property
    def unique_methods(self):
        if self._unique_methods is None:
            self._unique_methods = list(self._iterate_unique_methods())
        return self._unique_methods

    def get_method(self, name):
        return self._methods.get(name)

    def add_method(self, name, payload):
        method = murano_method.MuranoMethod(self, name, payload)
        self._methods[name] = method
        self._unique_methods = None
        return method

    @property
    def properties(self):
        return self._properties.keys()

    def register_methods(self, context):
        for method in self.unique_methods:
            context.register_function(
                method.yaql_function_definition,
                name=method.yaql_function_definition.name)

    def add_property(self, name, property_typespec):
        if not isinstance(property_typespec, typespec.PropertySpec):
            raise TypeError('property_typespec')
        self._properties[name] = property_typespec

    def get_property(self, name):
        return self._properties[name]

    def _find_method_chains(self, name):
        initial = [self.methods[name]] if name in self.methods else []
        yielded = False
        for parent in self.parents:
            for seq in parent._find_method_chains(name):
                yield initial + list(seq)
                yielded = True
        if initial and not yielded:
            yield initial

    def find_method(self, name):
        if name in self._methods:
            return [(self, name)]
        if not self._parents:
            return []
        return list(set(reduce(
            lambda x, y: x + y,
            [p.find_method(name) for p in self._parents])))

    def find_single_method(self, name):
        chains = sorted(self._find_method_chains(name), key=lambda t: len(t))
        result = []

        for i in range(len(chains)):
            if chains[i][0] in result:
                continue
            add = True
            for j in range(i + 1, len(chains)):
                common = 0
                if not add:
                    break
                for p in range(len(chains[i])):
                    if chains[i][-p - 1] is chains[j][-p - 1]:
                        common += 1
                    else:
                        break
                if common == len(chains[i]):
                    add = False
                    break
            if add:
                result.append(chains[i][0])
        if len(result) < 1:
            raise exceptions.NoMethodFound(name)
        elif len(result) > 1:
            raise exceptions.AmbiguousMethodName(name)
        return result[0]

    def find_all_methods(self, name):
        result = []
        queue = collections.deque([self])
        while queue:
            c = queue.popleft()
            if name in c.methods:
                method = c.methods[name]
                if method not in result:
                    result.append(method)
            queue.extend(c.parents)
        return result

    def _iterate_unique_methods(self):
        names = set()
        queue = collections.deque([self])
        while queue:
            c = queue.popleft()
            names.update(c.methods.keys())
            queue.extend(c.parents)
        for name in names:
            yield self.find_single_method(name)

    def find_property(self, name):
        result = []
        types = collections.deque([self])
        while len(types) > 0:
            mc = types.popleft()
            if name in mc.properties and mc not in result:
                result.append(mc)
            types.extend(mc.parents)
        return result

    def invoke(self, name, executor, this, args, kwargs, context=None):
        method = self.find_single_method(name)
        return method.invoke(executor, this, args, kwargs, context)

    def is_compatible(self, obj):
        if isinstance(obj, (murano_object.MuranoObject,
                            dsl.MuranoObjectInterface)):
            return self.is_compatible(obj.type)
        if obj is self:
            return True
        for parent in obj.parents:
            if self.is_compatible(parent):
                return True
        return False

    def new(self, owner, object_store, context=None, **kwargs):
        if context is None:
            context = object_store.context
        obj = murano_object.MuranoObject(
            self, owner, object_store.context, **kwargs)

        def initializer(**params):
            init_context = context.create_child_context()
            init_context['?allowPropertyWrites'] = True
            obj.initialize(init_context, object_store, params)
            return obj

        initializer.object = obj
        return initializer

    def __str__(self):
        return 'MuranoClass({0})'.format(self.name)
