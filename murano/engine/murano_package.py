# Copyright (c) 2014 Mirantis Inc.
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

import json
import os

from oslo_config import cfg
import yaml

from murano.dsl import murano_package

CONF = cfg.CONF


class MuranoPackage(murano_package.MuranoPackage):
    def __init__(self, package_loader, application_package):
        self.application_package = application_package
        super(MuranoPackage, self).__init__(
            package_loader,
            application_package.full_name,
            application_package.version,
            application_package.runtime_version,
            application_package.requirements
        )

    def get_class_config(self, name):
        json_config = os.path.join(CONF.engine.class_configs, name + '.json')
        if os.path.exists(json_config):
            with open(json_config) as f:
                return json.load(f)
        yaml_config = os.path.join(CONF.engine.class_configs, name + '.yaml')
        if os.path.exists(yaml_config):
            with open(yaml_config) as f:
                return yaml.safe_load(f)
        return {}

    def get_resource(self, name):
        return self.application_package.get_resource(name)
