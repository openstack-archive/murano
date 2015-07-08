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

from murano.engine import package_loader
from murano.packages import mpl_package
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
        cls.loader.loader_from_api = cls.api_loader

        cls.local_pkg_name = 'io.murano.test.MyTest'
        cls.api_pkg_name = 'test.mpl.v1.app.Thing'

    def test_loaders_initialized(self):
        self.assertEqual(1, len(self.loader.loaders_from_dir),
                         'One directory class loader should be initialized'
                         ' since there is one valid murano pl package in the'
                         ' provided directory in config.')
        self.assertIsInstance(self.loader.loaders_from_dir[0],
                              package_loader.DirectoryPackageLoader)

    def test_get_package_by_class_directory_loader(self):
        result = self.loader.get_package_by_class(self.local_pkg_name)
        self.assertIsInstance(result, mpl_package.MuranoPlPackage)

    def test_get_package_by_name_directory_loader(self):
        result = self.loader.get_package(self.local_pkg_name)
        self.assertIsInstance(result, mpl_package.MuranoPlPackage)

    def test_get_package_by_class_api_loader(self):
        self.loader.get_package(self.api_pkg_name)

        self.api_loader.get_package.assert_called_with(self.api_pkg_name)

    def test_get_package_api_loader(self):
        self.loader.get_package_by_class(self.api_pkg_name)

        self.api_loader.get_package_by_class.assert_called_with(
            self.api_pkg_name)
