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
import warnings
import weakref

import debtcollector
import semantic_version
import six
from yaql.language import specs
from yaql.language import utils

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import meta as dslmeta
from murano.dsl import murano_object
from murano.dsl import murano_type
from murano.dsl import namespace_resolver
from murano.dsl import principal_objects
from murano.dsl import yaql_integration


class MuranoPackage(dsl_types.MuranoPackage, dslmeta.MetaProvider):
    def __init__(self, package_loader, name, version=None,
                 runtime_version=None, requirements=None, meta=None):
        super(MuranoPackage, self).__init__()
        self._package_loader = weakref.proxy(package_loader)
        self._name = name
        self._version = helpers.parse_version(version)
        self._runtime_version = helpers.parse_version(runtime_version)
        self._requirements = {
            name: semantic_version.Spec('==' + str(self._version.major))
        }
        if name != constants.CORE_LIBRARY:
            self._requirements[constants.CORE_LIBRARY] = \
                semantic_version.Spec('==0')
        self._classes = {}
        self._imported_types = {object, murano_object.MuranoObject}
        for key, value in (requirements or {}).items():
            self._requirements[key] = helpers.parse_version_spec(value)

        self._load_queue = {}
        self._native_load_queue = {}
        if self.name == constants.CORE_LIBRARY:
            principal_objects.register(self)
        self._package_class = self._create_package_class()
        self._meta = lambda: dslmeta.MetaData(
            meta, dsl_types.MetaTargets.Package, self._package_class)

    @property
    def package_loader(self):
        return self._package_loader

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def runtime_version(self):
        return self._runtime_version

    @property
    def requirements(self):
        return self._requirements

    @property
    def classes(self):
        return set(self._classes.keys()).union(
            self._load_queue.keys()).union(self._native_load_queue.keys())

    def get_resource(self, name):
        raise NotImplementedError('resource API is not implemented')

    # noinspection PyMethodMayBeStatic
    def get_class_config(self, name):
        return {}

    def _register_mpl_classes(self, data, name=None):
        type_obj = self._classes.get(name)
        if type_obj is not None:
            return type_obj
        if callable(data):
            data = data()
        data = helpers.list_value(data)
        unnamed_class = None
        last_ns = {}
        for cls_data in data:
            last_ns = cls_data.setdefault('Namespaces', last_ns.copy())
            if len(cls_data) == 1:
                continue
            cls_name = cls_data.get('Name')
            if not cls_name:
                if unnamed_class:
                    raise exceptions.AmbiguousClassName(name)
                unnamed_class = cls_data
            else:
                ns_resolver = namespace_resolver.NamespaceResolver(last_ns)
                cls_name = ns_resolver.resolve_name(cls_name)
                if cls_name == name:
                    type_obj = murano_type.create(
                        cls_data, self, cls_name, ns_resolver)
                    self._classes[name] = type_obj
                else:
                    self._load_queue.setdefault(cls_name, cls_data)
        if type_obj is None and unnamed_class:
            unnamed_class['Name'] = name
            return self._register_mpl_classes(unnamed_class, name)
        return type_obj

    def _register_native_class(self, cls, name):
        if cls in self._imported_types:
            return self._classes[name]

        try:
            m_class = self.find_class(name, False)
        except exceptions.NoClassFound:
            m_class = self._register_mpl_classes({'Name': name}, name)

        m_class.extension_class = cls

        for method_name in dir(cls):
            if method_name.startswith('_'):
                continue
            method = getattr(cls, method_name)
            if not any((
                    helpers.inspect_is_method(cls, method_name),
                    helpers.inspect_is_static(cls, method_name),
                    helpers.inspect_is_classmethod(cls, method_name))):
                continue
            method_name_alias = (getattr(
                method, '__murano_name', None) or
                specs.convert_function_name(
                    method_name, yaql_integration.CONVENTION))
            m_class.add_method(method_name_alias, method, method_name)
        self._imported_types.add(cls)
        return m_class

    def register_class(self, cls, name=None):
        if inspect.isclass(cls):
            name = name or getattr(cls, '__murano_name', None) or cls.__name__
            if name in self._classes:
                self._register_native_class(cls, name)
            else:
                self._native_load_queue.setdefault(name, cls)
        elif isinstance(cls, dsl_types.MuranoType):
            self._classes[cls.name] = cls
        elif name not in self._classes:
            self._load_queue[name] = cls

    def find_class(self, name, search_requirements=True):
        payload = self._native_load_queue.pop(name, None)
        if payload is not None:
            return self._register_native_class(payload, name)

        payload = self._load_queue.pop(name, None)
        if payload is not None:
            result = self._register_mpl_classes(payload, name)
            if result:
                return result

        result = self._classes.get(name)
        if result:
            return result
        if search_requirements:
            pkgs_for_search = []
            for package_name, version_spec in self._requirements.items():
                if package_name == self.name:
                    continue
                referenced_package = self._package_loader.load_package(
                    package_name, version_spec)
                try:
                    return referenced_package.find_class(name, False)
                except exceptions.NoClassFound:
                    if name.startswith('io.murano.extensions'):
                        try:
                            short_name = name.replace(
                                'io.murano.extensions.', '', 1)
                            result = referenced_package.find_class(
                                short_name, False)
                            warnings.simplefilter("once")
                            msg = ("Plugin %(name)s was not found, but a "
                                   "%(shorter_name)s was found instead and "
                                   "will be used. This could be caused by "
                                   "recent change in plugin naming scheme. If "
                                   "you are developing applications targeting "
                                   "this plugin consider changing its name" %
                                   {'name': name, 'shorter_name': short_name})
                            debtcollector.deprecate(msg)
                            return result
                        except exceptions.NoClassFound:
                            pass
                    pkgs_for_search.append(referenced_package)
                    continue
            raise exceptions.NoClassFound(
                name, packages=pkgs_for_search + [self])

        raise exceptions.NoClassFound(name, packages=[self])

    @property
    def context(self):
        return None

    def _create_package_class(self):
        ns_resolver = namespace_resolver.NamespaceResolver(None)
        return murano_type.MuranoClass(
            ns_resolver, self.name, self, utils.NO_VALUE)

    def get_meta(self, context):
        if six.callable(self._meta):
            executor = helpers.get_executor()
            context = executor.create_package_context(self)
            self._meta = self._meta().get_meta(context)
        return self._meta

    def __repr__(self):
        return 'MuranoPackage({name})'.format(name=self.name)
