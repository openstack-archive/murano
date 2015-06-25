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

import os
import sys

import yaml

import murano.packages.application_package
from murano.packages import exceptions


class MuranoPlPackage(murano.packages.application_package.ApplicationPackage):
    def __init__(self, source_directory, manifest, loader):
        super(MuranoPlPackage, self).__init__(
            source_directory, manifest, loader)

        self._classes = None
        self._ui = None
        self._ui_cache = None
        self._raw_ui_cache = None
        self._classes_cache = {}

    @property
    def classes(self):
        return tuple(self._classes.keys())

    @property
    def ui(self):
        if not self._ui_cache:
            self._load_ui(True)
        return self._ui_cache

    @property
    def raw_ui(self):
        if not self._raw_ui_cache:
            self._load_ui(False)
        return self._raw_ui_cache

    def get_class(self, name):
        if name not in self._classes_cache:
            self._load_class(name)
        return self._classes_cache[name]

    # Private methods
    def _load_ui(self, load_yaml=False):
        if self._raw_ui_cache and load_yaml:
            self._ui_cache = yaml.load(self._raw_ui_cache, self.yaml_loader)
        else:
            ui_file = self._ui
            full_path = os.path.join(self._source_directory, 'UI', ui_file)
            if not os.path.isfile(full_path):
                self._raw_ui_cache = None
                self._ui_cache = None
                return
            try:
                with open(full_path) as stream:
                    self._raw_ui_cache = stream.read()
                    if load_yaml:
                        self._ui_cache = yaml.load(self._raw_ui_cache,
                                                   self.yaml_loader)
            except Exception as ex:
                trace = sys.exc_info()[2]
                raise exceptions.PackageUILoadError(str(ex)), None, trace

    def _load_class(self, name):
        if name not in self._classes:
            raise exceptions.PackageClassLoadError(
                name, 'Class not defined in this package')
        def_file = self._classes[name]
        full_path = os.path.join(self._source_directory, 'Classes', def_file)
        if not os.path.isfile(full_path):
            raise exceptions.PackageClassLoadError(
                name, 'File with class definition not found')
        try:
            with open(full_path) as stream:
                self._classes_cache[name] = yaml.load(stream, self.yaml_loader)
        except Exception as ex:
            trace = sys.exc_info()[2]
            msg = 'Unable to load class definition due to "{0}"'.format(
                str(ex))
            raise exceptions.PackageClassLoadError(name, msg), None, trace

    def validate(self):
        self._classes_cache.clear()
        for class_name in self._classes:
            self.get_class(class_name)
        self._load_ui(True)
        super(MuranoPlPackage, self).validate()
