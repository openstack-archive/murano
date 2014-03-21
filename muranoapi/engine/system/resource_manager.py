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
import os.path
import yaml as yamllib

from muranoapi.engine import objects


class ResourceManager(objects.MuranoObject):
    def initialize(self, base_path, _context, _class):
        if _class is None:
            _class = _context.get_data('$')
        class_name = _class.type.name
        self._base_path = os.path.join(base_path, class_name, 'resources')

    def string(self, name):
        path = os.path.join(self._base_path, name)
        with open(path) as file:
            return file.read()

    def json(self, name):
        return jsonlib.loads(self.string(name))

    def yaml(self, name):
        return yamllib.safe_load(self.string(name))
