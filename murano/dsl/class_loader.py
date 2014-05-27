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

import inspect
import types

import yaql
import yaql.context

import murano.dsl.exceptions as exceptions
import murano.dsl.helpers as helpers
import murano.dsl.murano_class as murano_class
import murano.dsl.murano_object as murano_object
import murano.dsl.namespace_resolver as namespace_resolver
import murano.dsl.principal_objects as principal_objects
import murano.dsl.typespec as typespec


class MuranoClassLoader(object):
    def __init__(self):
        self._loaded_types = {}
        self._packages_cache = {}
        principal_objects.register(self)

    def _get_package(self, class_name):
        package_name = self.find_package_name(class_name)
        if package_name is None:
            raise exceptions.NoPackageForClassFound(class_name)
        if package_name not in self._packages_cache:
            package = self.load_package(package_name)
            self._packages_cache[package_name] = package
        return self._packages_cache[package_name]

    def get_class(self, name, create_missing=False):
        if name in self._loaded_types:
            return self._loaded_types[name]

        try:
            data = self.load_definition(name)
            package = self._get_package(name)
        except (exceptions.NoPackageForClassFound, exceptions.NoClassFound):
            if create_missing:
                data = {'Name': name}
                package = None
            else:
                raise

        namespaces = data.get('Namespaces', {})
        ns_resolver = namespace_resolver.NamespaceResolver(namespaces)

        class_parents = data.get('Extends')
        if class_parents:
            if not isinstance(class_parents, types.ListType):
                class_parents = [class_parents]
            for i, parent_name in enumerate(class_parents):
                full_name = ns_resolver.resolve_name(parent_name)
                class_parents[i] = self.get_class(full_name)

        type_obj = murano_class.MuranoClass(self, ns_resolver, name,
                                            package, class_parents)

        properties = data.get('Properties', {})
        for property_name, property_spec in properties.iteritems():
            spec = typespec.PropertySpec(property_spec, ns_resolver)
            type_obj.add_property(property_name, spec)

        for method_name, payload in data.get('Workflow', {}).iteritems():
            type_obj.add_method(method_name, payload)

        self._loaded_types[name] = type_obj
        return type_obj

    def load_definition(self, name):
        raise NotImplementedError()

    def find_package_name(self, class_name):
        raise NotImplementedError()

    def load_package(self, class_name):
        raise NotImplementedError()

    def create_root_context(self):
        return yaql.create_context(True)

    def create_local_context(self, parent_context, murano_class):
        return yaql.context.Context(parent_context=parent_context)

    def _fix_parameters(self, kwargs):
        result = {}
        for key, value in kwargs.iteritems():
            if key in ('class', 'for', 'from', 'is', 'lambda', 'as',
                       'exec', 'assert', 'and', 'or', 'break', 'def',
                       'del', 'try', 'while', 'yield', 'raise', 'while',
                       'pass', 'return', 'not', 'print', 'in', 'import',
                       'global', 'if', 'finally', 'except', 'else', 'elif',
                       'continue', 'yield'):
                key = '_' + key
            result[key] = value
        return result

    def import_class(self, cls, name=None):
        if not name:
            if inspect.isclass(cls):
                name = cls._murano_class_name
            else:
                name = cls.__class__._murano_class_name

        m_class = self.get_class(name, create_missing=True)
        if inspect.isclass(cls):
            if issubclass(cls, murano_object.MuranoObject):
                m_class.object_class = cls
            else:
                mpc_name = 'mpc' + helpers.generate_id()
                bases = (cls, murano_object.MuranoObject)
                m_class.object_class = type(mpc_name, bases, {})

        for item in dir(cls):
            method = getattr(cls, item)
            if ((inspect.isfunction(method) or inspect.ismethod(method)) and
                    not item.startswith('_')):
                m_class.add_method(item, method)
