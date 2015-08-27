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

from murano.dsl import exceptions
from murano.dsl import murano_class
from murano.dsl import murano_object
from murano.dsl import namespace_resolver
from murano.dsl import principal_objects
from murano.dsl import typespec
from murano.dsl import yaql_integration


class MuranoClassLoader(object):
    def __init__(self):
        self._loaded_types = {}
        self._packages_cache = {}
        self._imported_types = {object, murano_object.MuranoObject}
        principal_objects.register(self)

    def _get_package_for_class(self, class_name):
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
            package = self._get_package_for_class(name)
        except (exceptions.NoPackageForClassFound, exceptions.NoClassFound):
            if create_missing:
                data = {'Name': name}
                package = None
            else:
                raise

        namespaces = data.get('Namespaces') or {}
        ns_resolver = namespace_resolver.NamespaceResolver(namespaces)

        parent_class_names = data.get('Extends')
        parent_classes = []
        if parent_class_names:
            if not isinstance(parent_class_names, types.ListType):
                parent_class_names = [parent_class_names]
            for parent_name in parent_class_names:
                full_name = ns_resolver.resolve_name(parent_name)
                parent_classes.append(self.get_class(full_name))

        type_obj = murano_class.MuranoClass(self, ns_resolver, name,
                                            package, parent_classes)

        properties = data.get('Properties') or {}
        for property_name, property_spec in properties.iteritems():
            spec = typespec.PropertySpec(property_spec, type_obj)
            type_obj.add_property(property_name, spec)

        methods = data.get('Methods') or data.get('Workflow') or {}

        method_mappings = {
            'initialize': '.init',
            'destroy': '.destroy'
        }

        for method_name, payload in methods.iteritems():
            type_obj.add_method(
                method_mappings.get(method_name, method_name), payload)

        self._loaded_types[name] = type_obj
        return type_obj

    def load_definition(self, name):
        raise NotImplementedError()

    def find_package_name(self, class_name):
        raise NotImplementedError()

    def load_package(self, class_name):
        raise NotImplementedError()

    def create_root_context(self):
        return yaql_integration.create_context()

    def get_class_config(self, name):
        return {}

    def create_local_context(self, parent_context, murano_class):
        return parent_context.create_child_context()

    def import_class(self, cls, name=None):
        if cls in self._imported_types:
            return

        name = name or getattr(cls, '__murano_name', None) or cls.__name__
        m_class = self.get_class(name, create_missing=True)
        m_class.extend_with_class(cls)

        for method_name in dir(cls):
            if method_name.startswith('_'):
                continue
            method = getattr(cls, method_name)
            if not inspect.ismethod(method):
                continue
            m_class.add_method(
                yaql_integration.CONVENTION.convert_function_name(
                    method_name),
                method)
        self._imported_types.add(cls)
