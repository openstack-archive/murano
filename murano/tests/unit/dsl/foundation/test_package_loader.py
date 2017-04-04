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

import os.path


from murano.dsl import constants
from murano.dsl import murano_package
from murano.dsl import namespace_resolver
from murano.dsl import package_loader
from murano.engine import yaql_yaml_loader
from murano.tests.unit.dsl.foundation import object_model
from oslo_utils import fnmatch


class TestPackage(murano_package.MuranoPackage):
    def __init__(self, pkg_loader, name, version,
                 runtime_version, requirements, configs, meta):
        self.__configs = configs
        super(TestPackage, self).__init__(
            pkg_loader, name, version,
            runtime_version, requirements, meta)

    def get_class_config(self, name):
        return self.__configs.get(name, {})

    def get_resource(self, name):
        pass


class TestPackageLoader(package_loader.MuranoPackageLoader):
    _classes_cache = {}

    def __init__(self, directory, package_name, parent_loader=None, meta=None):
        self._package_name = package_name
        self._yaml_loader = yaql_yaml_loader.get_loader('1.0')
        if directory in TestPackageLoader._classes_cache:
            self._classes = TestPackageLoader._classes_cache[directory]
        else:
            self._classes = {}
            self._build_index(directory)
            TestPackageLoader._classes_cache[directory] = self._classes
        self._parent = parent_loader
        self._configs = {}
        self._package = TestPackage(
            self, package_name, None, constants.RUNTIME_VERSION_1_0,
            None, self._configs, meta)
        for name, payload in self._classes.items():
            self._package.register_class(payload, name)
        super(TestPackageLoader, self).__init__()

    def load_package(self, package_name, version_spec):
        if package_name == self._package_name:
            return self._package
        elif self._parent:
            return self._parent.load_package(package_name, version_spec)
        else:
            raise KeyError(package_name)

    def load_class_package(self, class_name, version_spec):
        if class_name in self._classes:
            return self._package
        elif self._parent:
            return self._parent.load_class_package(class_name, version_spec)
        else:
            raise KeyError(class_name)

    def export_fixation_table(self):
        return {}

    def import_fixation_table(self, fixations):
        pass

    def compact_fixation_table(self):
        pass

    def _build_index(self, directory):
        yamls = [
            os.path.join(dirpath, f)
            for dirpath, _, files in os.walk(directory)
            for f in fnmatch.filter(files, '*.yaml')
            if f != 'manifest.yaml'
        ]
        for class_def_file in yamls:
            self._load_classes(class_def_file)

    def _load_classes(self, class_def_file):
        with open(class_def_file, 'rb') as stream:
            data_lst = self._yaml_loader(stream.read(), class_def_file)

        last_ns = {}
        for data in data_lst:
            last_ns = data.get('Namespaces', last_ns.copy())
            if 'Name' not in data:
                continue

            for name, method in (data.get('Methods') or data.get(
                    'Workflow') or {}).items():
                if name.startswith('test'):
                    method['Scope'] = 'Public'

            ns = namespace_resolver.NamespaceResolver(last_ns)
            class_name = ns.resolve_name(data['Name'])
            self._classes[class_name] = data_lst

    def set_config_value(self, class_name, property_name, value):
        if isinstance(class_name, object_model.Object):
            class_name = class_name.type_name
        self._configs.setdefault(class_name, {})[
            property_name] = value

    def register_package(self, package):
        super(TestPackageLoader, self).register_package(package)
