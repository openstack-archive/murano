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
import weakref

import semantic_version

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import murano_class
from murano.dsl import murano_object
from murano.dsl import principal_objects
from murano.dsl import yaql_integration


class MuranoPackage(dsl_types.MuranoPackage):
    def __init__(self, package_loader, name, version=None,
                 runtime_version=None, requirements=None):
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
        for key, value in (requirements or {}).iteritems():
            self._requirements[key] = helpers.parse_version_spec(value)

        self._load_queue = {}
        self._native_load_queue = {}
        if self.name == constants.CORE_LIBRARY:
            principal_objects.register(self)

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
        return set(self._classes.keys() +
                   self._load_queue.keys() +
                   self._native_load_queue.keys())

    def get_resource(self, name):
        raise NotImplementedError('resource API is not implemented')

    # noinspection PyMethodMayBeStatic
    def get_class_config(self, name):
        return {}

    def _register_mpl_class(self, data, name=None):
        type_obj = self._classes.get(name)
        if not type_obj:
            type_obj = murano_class.MuranoClass.create(data, self, name)
            self._classes[name] = type_obj
        return type_obj

    def _register_native_class(self, cls, name):
        if cls in self._imported_types:
            return self._classes[name]

        try:
            m_class = self.find_class(name, False)
        except exceptions.NoClassFound:
            m_class = self._register_mpl_class({'Name': name}, name)

        m_class.extend_with_class(cls)

        for method_name in dir(cls):
            if method_name.startswith('_'):
                continue
            method = getattr(cls, method_name)
            if not inspect.ismethod(method):
                continue
            # TODO(slagun): update the code below to use yaql native
            # method for this when https://review.openstack.org/#/c/220748/
            # will get merged and Murano requirements bump to corresponding
            # yaql version
            method_name_alias = (getattr(
                method, '__murano_name', None) or
                yaql_integration.CONVENTION.convert_function_name(
                    method_name.rstrip('_')))
            m_class.add_method(method_name_alias, method)
        self._imported_types.add(cls)
        return m_class

    def register_class(self, cls, name=None):
        if inspect.isclass(cls):
            name = name or getattr(cls, '__murano_name', None) or cls.__name__
            self._native_load_queue[name] = cls
        elif isinstance(cls, murano_class.MuranoClass):
            self._classes[cls.name] = cls
        else:
            self._load_queue[name] = cls

    def find_class(self, name, search_requirements=True):
        payload = self._native_load_queue.pop(name, None)
        if payload is not None:
            return self._register_native_class(payload, name)

        payload = self._load_queue.pop(name, None)
        if payload is not None:
            if callable(payload):
                payload = payload()
            return self._register_mpl_class(payload, name)

        result = self._classes.get(name)
        if result:
            return result

        if search_requirements:
            for package_name, version_spec in self._requirements.iteritems():
                if package_name == self.name:
                    continue
                referenced_package = self._package_loader.load_package(
                    package_name, version_spec)
                try:
                    return referenced_package.find_class(name, False)
                except exceptions.NoClassFound:
                    continue
        raise exceptions.NoClassFound(name)

    @property
    def context(self):
        return None
