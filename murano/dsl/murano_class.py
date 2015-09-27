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
import weakref

import semantic_version
from yaql.language import utils

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import murano_method
from murano.dsl import murano_object
from murano.dsl import namespace_resolver
from murano.dsl import typespec
from murano.dsl import yaql_integration


class MuranoClass(dsl_types.MuranoClass):
    def __init__(self, ns_resolver, name, package, parents=None):
        self._package = weakref.ref(package)
        self._methods = {}
        self._namespace_resolver = ns_resolver
        self._name = name
        self._properties = {}
        self._config = {}
        if self._name == constants.CORE_LIBRARY_OBJECT:
            self._parents = []
        else:
            self._parents = parents or [
                package.find_class(constants.CORE_LIBRARY_OBJECT)]
        self._context = None
        self._parent_mappings = self._build_parent_remappings()

    @classmethod
    def create(cls, data, package, name=None):
        namespaces = data.get('Namespaces') or {}
        ns_resolver = namespace_resolver.NamespaceResolver(namespaces)

        if not name:
            name = ns_resolver.resolve_name(data['Name'])

        parent_class_names = data.get('Extends')
        parent_classes = []
        if parent_class_names:
            if not utils.is_sequence(parent_class_names):
                parent_class_names = [parent_class_names]
            for parent_name in parent_class_names:
                full_name = ns_resolver.resolve_name(parent_name)
                parent_classes.append(package.find_class(full_name))

        type_obj = cls(ns_resolver, name, package, parent_classes)

        properties = data.get('Properties') or {}
        for property_name, property_spec in properties.iteritems():
            spec = typespec.PropertySpec(
                property_name, property_spec, type_obj)
            type_obj.add_property(property_name, spec)

        methods = data.get('Methods') or data.get('Workflow') or {}

        method_mappings = {
            'initialize': '.init',
            'destroy': '.destroy'
        }

        for method_name, payload in methods.iteritems():
            type_obj.add_method(
                method_mappings.get(method_name, method_name), payload)

        return type_obj

    @property
    def name(self):
        return self._name

    @property
    def package(self):
        return self._package()

    @property
    def namespace_resolver(self):
        return self._namespace_resolver

    @property
    def declared_parents(self):
        return self._parents

    @property
    def methods(self):
        return self._methods

    @property
    def parent_mappings(self):
        return self._parent_mappings

    def extend_with_class(self, cls):
        ctor = yaql_integration.get_class_factory_definition(cls, self)
        self.add_method('__init__', ctor)

    def get_method(self, name):
        return self._methods.get(name)

    def add_method(self, name, payload):
        method = murano_method.MuranoMethod(self, name, payload)
        self._methods[name] = method
        self._context = None
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

    def _find_method_chains(self, name, origin):
        queue = collections.deque([(self, ())])
        while queue:
            cls, path = queue.popleft()
            segment = (cls.methods[name],) if name in cls.methods else ()
            leaf = True
            for p in cls.parents(origin):
                leaf = False
                queue.append((p, path + segment))
            if leaf:
                path = path + segment
                if path:
                    yield path

    def find_single_method(self, name):
        chains = sorted(self._find_method_chains(name, self),
                        key=lambda t: len(t))
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

    def find_methods(self, predicate):
        result = []
        for c in self.ancestors():
            for method in c.methods.itervalues():
                if predicate(method) and method not in result:
                    result.append(method)
        return result

    def _iterate_unique_methods(self):
        names = set()
        for c in self.ancestors():
            names.update(c.methods.keys())
        for name in names:
            try:
                yield self.find_single_method(name)
            except exceptions.AmbiguousMethodName as e:
                def func(*args, **kwargs):
                    raise e
                yield murano_method.MuranoMethod(self, name, func)

    def find_property(self, name):
        result = []
        for mc in self.ancestors():
            if name in mc.properties and mc not in result:
                result.append(mc)
        return result

    def find_single_property(self, name):
        result = None
        parents = None
        gen = helpers.traverse(self)
        while True:
            try:
                mc = gen.send(parents)
                if name in mc.properties:
                    if result and result != mc:
                        raise exceptions.AmbiguousPropertyNameError(name)
                    result = mc
                    parents = []
                else:
                    parents = mc.parents(self)
            except StopIteration:
                return result

    def invoke(self, name, executor, this, args, kwargs, context=None):
        method = self.find_single_method(name)
        return method.invoke(executor, this, args, kwargs, context)

    def is_compatible(self, obj):
        if isinstance(obj, (murano_object.MuranoObject,
                            dsl.MuranoObjectInterface)):
            obj = obj.type
        return any(cls is self for cls in obj.ancestors())

    def new(self, owner, object_store, **kwargs):
        obj = murano_object.MuranoObject(self, owner, object_store, **kwargs)

        def initializer(__context, **params):
            if __context is None:
                __context = object_store.executor.create_object_context(obj)
            init_context = __context.create_child_context()
            init_context[constants.CTX_ALLOW_PROPERTY_WRITES] = True
            obj.initialize(init_context, object_store, params)
            return obj

        initializer.object = obj
        return initializer

    def __repr__(self):
        return 'MuranoClass({0}/{1})'.format(self.name, self.version)

    @property
    def version(self):
        return self.package.version

    def _build_parent_remappings(self):
        """Remaps class parents.

        In case of multiple inheritance class may indirectly get several
        versions of the same class. It is reasonable to try to replace them
        with single version to avoid conflicts. We can do that when within
        versions that satisfy our class package requirements.
        But in order to merge several classes that are not our parents but
        grand parents we will need to modify classes that may be used
        somewhere else (with another set of requirements). We cannot do this.
        So instead we build translation table that will tell which ancestor
        class need to be replaced with which so that we minimize number of
        versions used for single class (or technically packages since version
        is a package attribute). For translation table to work there should
        be a method that returns all class virtual ancestors so that everybody
        will see them instead of accessing class parents directly and getting
        declared ancestors.
        """
        result = {}

        aggregation = {
            self.package.name: {(
                self.package,
                semantic_version.Spec('==' + str(self.package.version))
            )}
        }
        for cls, parent in helpers.traverse(
                ((self, parent) for parent in self._parents),
                lambda (c, p): ((p, anc) for anc in p.declared_parents)):
            if cls.package != parent.package:
                requirement = cls.package.requirements[parent.package.name]
                aggregation.setdefault(parent.package.name, set()).add(
                    (parent.package, requirement))

        package_bindings = {}
        for versions in aggregation.itervalues():
            mappings = self._remap_package(versions)
            package_bindings.update(mappings)

        for cls in helpers.traverse(
                self.declared_parents, lambda c: c.declared_parents):
            if cls.package in package_bindings:
                package2 = package_bindings[cls.package]
                cls2 = package2.classes[cls.name]
                result[cls] = cls2
        return result

    @staticmethod
    def _remap_package(versions):
        result = {}
        reverse_mappings = {}
        versions_list = sorted(versions, key=lambda x: x[0].version)
        i = 0
        while i < len(versions_list):
            package1, requirement1 = versions_list[i]
            dst_package = None
            for j, (package2, _) in enumerate(versions_list):
                if i == j:
                    continue
                if package2.version in requirement1 and (
                        dst_package is None or
                        dst_package.version < package2.version):
                    dst_package = package2
            if dst_package:
                result[package1] = dst_package
                reverse_mappings.setdefault(dst_package, []).append(package1)
                for package in reverse_mappings.get(package1, []):
                    result[package] = dst_package
                del versions_list[i]
            else:
                i += 1
        return result

    def parents(self, origin):
        mappings = origin.parent_mappings
        yielded = set()
        for p in self._parents:
            parent = mappings.get(p, p)
            if parent not in yielded:
                yielded.add(parent)
                yield parent

    def ancestors(self):
        for c in helpers.traverse(self, lambda t: t.parents(self)):
            yield c

    @property
    def context(self):
        if not self._context:
            self._context = yaql_integration.create_empty_context()
            for m in self._iterate_unique_methods():
                self._context.register_function(
                    m.yaql_function_definition,
                    name=m.yaql_function_definition.name)
        return self._context
