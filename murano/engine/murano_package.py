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
            application_package.requirements,
            application_package.meta
        )

    def get_class_config(self, name):
        version_parts = (
            str(self.version.major),
            str(self.version.minor),
            str(self.version.patch)
        )
        num_parts = len(version_parts)

        for i in range(num_parts + 1):
            for ext in ('json', 'yaml'):
                if i == num_parts:
                    if version_parts[0] == '0':
                        version_suffix = ''
                    else:
                        continue
                else:
                    version_suffix = '-' + '.'.join(
                        version_parts[:num_parts - i])
                file_name = '{name}{version}.{extension}'.format(
                    name=name, version=version_suffix, extension=ext)
                path = os.path.join(CONF.engine.class_configs, file_name)
                if os.path.exists(path):
                    if ext == 'json':
                        with open(path) as f:
                            return json.load(f)
                    else:
                        with open(path) as f:
                            return yaml.safe_load(f)
        return {}

    def get_resource(self, name):
        return self.application_package.get_resource(name)
