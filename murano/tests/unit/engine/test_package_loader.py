#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os

import mock
from oslo_config import cfg
import semantic_version

from murano.dsl import murano_package as dsl_package
from murano.engine import package_loader
from murano.tests.unit import base

CONF = cfg.CONF


class TestCombinedPackageLoader(base.MuranoTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCombinedPackageLoader, cls).setUpClass()

        location = os.path.dirname(__file__)
        CONF.set_override('load_packages_from', [location], 'engine')
        cls.murano_client_factory = mock.MagicMock()
        cls.loader = package_loader.CombinedPackageLoader(
            cls.murano_client_factory, 'test_tenant_id')
        cls.api_loader = mock.MagicMock()
        cls.loader.api_loader = cls.api_loader

        cls.local_pkg_name = 'io.murano.test.MyTest'
        cls.api_pkg_name = 'test.mpl.v1.app.Thing'

    def test_loaders_initialized(self):
        self.assertEqual(1, len(self.loader.directory_loaders),
                         'One directory class loader should be initialized'
                         ' since there is one valid murano pl package in the'
                         ' provided directory in config.')
        self.assertIsInstance(self.loader.directory_loaders[0],
                              package_loader.DirectoryPackageLoader)

    def test_get_package_by_class_directory_loader(self):
        spec = semantic_version.Spec('*')
        result = self.loader.load_class_package(self.local_pkg_name, spec)
        self.assertIsInstance(result, dsl_package.MuranoPackage)

    def test_get_package_by_name_directory_loader(self):
        spec = semantic_version.Spec('*')
        result = self.loader.load_package(self.local_pkg_name, spec)
        self.assertIsInstance(result, dsl_package.MuranoPackage)

    def test_get_package_by_class_api_loader(self):
        spec = semantic_version.Spec('*')
        self.loader.load_package(self.api_pkg_name, spec)

        self.api_loader.load_package.assert_called_with(
            self.api_pkg_name, spec)

    def test_get_package_api_loader(self):
        spec = semantic_version.Spec('*')
        self.loader.load_class_package(self.api_pkg_name, spec)

        self.api_loader.load_class_package.assert_called_with(
            self.api_pkg_name, spec)
