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
import os.path
import sys

from oslo.config import cfg
import yaml

from murano.dsl import class_loader
from murano.dsl import exceptions
from murano.dsl import murano_package
from murano.engine.system import yaql_functions
from murano.openstack.common import log as logging
from murano.packages import exceptions as pkg_exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PackageClassLoader(class_loader.MuranoClassLoader):
    def __init__(self, package_loader):
        self.package_loader = package_loader
        self._class_packages = {}
        super(PackageClassLoader, self).__init__()

    def _get_package_for(self, class_name):
        package = self._class_packages.get(class_name, None)
        if package is None:
            package = self.package_loader.get_package_by_class(class_name)
            if package is not None:
                for cn in package.classes:
                    self._class_packages[cn] = package
        return package

    def load_definition(self, name):
        try:
            package = self._get_package_for(name)
            if package is None:
                raise exceptions.NoPackageForClassFound(name)
            return package.get_class(name)
        # (sjmc7) This is used as a control condition for system classes;
        # do not delete (although I think it needs a better solution)
        except exceptions.NoPackageForClassFound:
            raise
        except Exception as e:
            msg = "Error loading {0}: {1}".format(name, str(e))
            raise pkg_exceptions.PackageLoadError(msg), None, sys.exc_info()[2]

    def load_package(self, name):
        package = murano_package.MuranoPackage()
        package.name = name
        return package

    def find_package_name(self, class_name):
        app_pkg = self._get_package_for(class_name)
        return None if app_pkg is None else app_pkg.full_name

    def create_root_context(self):
        context = super(PackageClassLoader, self).create_root_context()
        yaql_functions.register(context)
        return context

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
