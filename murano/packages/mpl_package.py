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

from murano.common.helpers import path
from murano.packages import exceptions
from murano.packages import package_base


class MuranoPlPackage(package_base.PackageBase):
    def __init__(self, format_name, runtime_version, source_directory,
                 manifest):
        super(MuranoPlPackage, self).__init__(
            format_name, runtime_version, source_directory, manifest)
        self._classes = manifest.get('Classes')
        self._ui_file = manifest.get('UI', 'ui.yaml')
        self._requirements = manifest.get('Require') or {}
        self._meta = manifest.get('Meta')

    @property
    def classes(self):
        return self._classes.keys()

    @property
    def ui(self):
        full_path = path.secure_join(
            self._source_directory, 'UI', self._ui_file)
        if not os.path.isfile(full_path):
            return None
        with open(full_path, 'rb') as stream:
            return stream.read()

    @property
    def requirements(self):
        return self._requirements

    def get_class(self, name):
        if name not in self._classes:
            raise exceptions.PackageClassLoadError(
                name, 'Class not defined in package ' + self.full_name)
        def_file = self._classes[name]
        full_path = path.secure_join(
            self._source_directory, 'Classes', def_file)
        if not os.path.isfile(full_path):
            raise exceptions.PackageClassLoadError(
                name, 'File with class definition not found')
        with open(full_path, 'rb') as stream:
            return stream.read(), full_path

    @property
    def meta(self):
        return self._meta
