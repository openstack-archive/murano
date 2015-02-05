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

import murano.dsl.helpers as helpers
import murano.dsl.murano_object as murano_object

if hasattr(yamllib, 'CSafeLoader'):
    yaml_loader = yamllib.CSafeLoader
else:
    yaml_loader = yamllib.SafeLoader


def _construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)

yaml_loader.add_constructor(u'tag:yaml.org,2002:str', _construct_yaml_str)
# Unquoted dates like 2013-05-23 in yaml files get loaded as objects of type
# datetime.data which causes problems in API layer when being processed by
# oslo.serialization.jsonutils. Therefore, make unicode string out of
# timestamps until jsonutils can handle dates.
yaml_loader.add_constructor(u'tag:yaml.org,2002:timestamp',
                            _construct_yaml_str)


class ResourceManager(murano_object.MuranoObject):
    def initialize(self, package_loader, _context):
        murano_class = helpers.get_type(_context)
        self._package = package_loader.get_package(murano_class.package.name)

    def string(self, name):
        path = self._package.get_resource(name)
        with open(path) as file:
            return file.read()

    def json(self, name):
        return jsonlib.loads(self.string(name))

    def yaml(self, name):
        return yamllib.load(self.string(name), Loader=yaml_loader)
