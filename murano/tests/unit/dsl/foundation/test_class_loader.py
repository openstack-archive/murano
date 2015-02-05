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

import fnmatch
import os.path

import yaml

from murano.dsl import class_loader
from murano.dsl import exceptions
from murano.dsl import murano_package
from murano.dsl import namespace_resolver
from murano.engine.system import yaql_functions
from murano.engine import yaql_yaml_loader
from murano.tests.unit.dsl.foundation import object_model


class TestClassLoader(class_loader.MuranoClassLoader):
    _classes_cache = {}
    _configs = {}

    def __init__(self, directory, package_name, parent_loader=None):
        self._package = murano_package.MuranoPackage()
        self._package.name = package_name
        self._parent = parent_loader
        if directory in TestClassLoader._classes_cache:
            self._classes = TestClassLoader._classes_cache[directory]
        else:
            self._classes = {}
            self._build_index(directory)
            TestClassLoader._classes_cache[directory] = self._classes
        self._functions = {}
        super(TestClassLoader, self).__init__()

    def find_package_name(self, class_name):
        if class_name in self._classes:
            return self._package.name
        if self._parent:
            return self._parent.find_package_name(class_name)
        return None

    def load_package(self, class_name):
        return self._package

    def load_definition(self, name):
        try:
            return self._classes[name]
        except KeyError:
            if self._parent:
                return self._parent.load_definition(name)
            raise exceptions.NoClassFound(name)

    def _build_index(self, directory):
        yamls = [os.path.join(dirpath, f)
                 for dirpath, dirnames, files in os.walk(directory)
                 for f in fnmatch.filter(files, '*.yaml')]
        for class_def_file in yamls:
            self._load_class(class_def_file)

    def _load_class(self, class_def_file):
        with open(class_def_file) as stream:
            data = yaml.load(stream, yaql_yaml_loader.YaqlYamlLoader)

        if 'Name' not in data:
            return

        for name, method in (data.get('Methods') or data.get(
                'Workflow') or {}).iteritems():
            if name.startswith('test'):
                method['Usage'] = 'Action'

        ns = namespace_resolver.NamespaceResolver(data.get('Namespaces', {}))
        class_name = ns.resolve_name(data['Name'])
        self._classes[class_name] = data

    def create_root_context(self):
        context = super(TestClassLoader, self).create_root_context()
        yaql_functions.register(context)
        for name, func in self._functions.iteritems():
            context.register_function(func, name)
        return context

    def register_function(self, func, name):
        self._functions[name] = func

    def get_class_config(self, name):
        return TestClassLoader._configs.get(name, {})

    def set_config_value(self, class_name, property_name, value):
        if isinstance(class_name, object_model.Object):
            class_name = class_name.type_name
        TestClassLoader._configs.setdefault(class_name, {})[
            property_name] = value

    @staticmethod
    def clear_configs():
        TestClassLoader._configs = {}
