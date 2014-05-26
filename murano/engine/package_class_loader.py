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

from oslo.config import cfg

from murano.dsl import class_loader
from murano.dsl import exceptions
from murano.dsl import murano_package
from murano.engine.system import yaql_functions
from murano.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PackageClassLoader(class_loader.MuranoClassLoader):
    def __init__(self, package_loader):
        self.package_loader = package_loader
        self._packages_cache = {}
        super(PackageClassLoader, self).__init__()

    def load_definition(self, name):
        try:
            package = self.package_loader.get_package_by_class(name)
            return package.get_class(name)
        except Exception:
            raise exceptions.NoClassFound(name)

    def load_package(self, name):
        package = murano_package.MuranoPackage()
        package.name = name
        return package

    def find_package_name(self, class_name):
        app_pkg = self.package_loader.get_package_by_class(class_name)
        return None if app_pkg is None else app_pkg.full_name

    def create_root_context(self):
        context = super(PackageClassLoader, self).create_root_context()
        yaql_functions.register(context)
        return context
