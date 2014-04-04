# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json as jsonlib
import yaml as yamllib

import muranoapi.dsl.murano_object as murano_object


class ResourceManager(murano_object.MuranoObject):
    def initialize(self, package_loader, _context, _class):
        if _class is None:
            _class = _context.get_data('$')
        self._package = package_loader.get_package(_class.type.package.name)

    def string(self, name):
        path = self._package.get_resource(name)
        with open(path) as file:
            return file.read()

    def json(self, name):
        return jsonlib.loads(self.string(name))

    def yaml(self, name):
        return yamllib.safe_load(self.string(name))
