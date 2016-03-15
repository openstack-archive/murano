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
import shutil
import tempfile

import mock
from oslo_config import cfg
import semantic_version
import testtools

from murano.dsl import murano_package as dsl_package
from murano.engine import package_loader
from murano.tests.unit import base
from murano_tempest_tests import utils

CONF = cfg.CONF


class TestPackageCache(base.MuranoTestCase):

    def setUp(self):
        super(TestPackageCache, self).setUp()

        self.location = tempfile.mkdtemp()
        CONF.set_override('enable_packages_cache', True, 'engine')
        self.old_location = CONF.engine.packages_cache
        CONF.set_override('packages_cache', self.location, 'engine')

        self.murano_client = mock.MagicMock()
        package_loader.ApiPackageLoader.client = self.murano_client
        self.loader = package_loader.ApiPackageLoader(None)

    def tearDown(self):
        CONF.set_override('packages_cache', self.old_location, 'engine')
        shutil.rmtree(self.location, ignore_errors=True)
        super(TestPackageCache, self).tearDown()

    @testtools.skipIf(os.name == 'nt', "Doesn't work on Windows")
    def test_load_package(self):
        fqn = 'io.murano.apps.test'
        path, name = utils.compose_package(
            'test',
            os.path.join(self.location, 'manifest.yaml'),
            self.location, archive_dir=self.location)
        with open(path, 'rb') as f:
            package_data = f.read()
        spec = semantic_version.Spec('*')

        first_id, second_id, third_id = '123', '456', '789'
        package = mock.MagicMock()
        package.fully_qualified_name = fqn
        package.id = first_id
        package.version = '0.0.1'

        self.murano_client.packages.filter = mock.MagicMock(
            return_value=[package])
        self.murano_client.packages.download = mock.MagicMock(
            return_value=package_data)

        # load the package
        self.loader.load_class_package(fqn, spec)

        # assert that everything got created
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn)))
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version)))
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version, first_id)))
        self.assertTrue(os.path.isfile(os.path.join(
            self.location, fqn, package.version, first_id, 'manifest.yaml')))

        # assert, that we called download
        self.assertEqual(self.murano_client.packages.download.call_count, 1)

        # now that the cache is in place, call it for the 2d time
        self.loader._package_cache = {}
        self.loader._class_cache = {}
        self.loader.load_class_package(fqn, spec)

        # check that we didn't download a thing
        self.assertEqual(self.murano_client.packages.download.call_count, 1)

        # changing id, new package would be downloaded.
        package.id = second_id
        self.loader._package_cache = {}
        self.loader._class_cache = {}
        self.loader.load_class_package(fqn, spec)

        # check that we didn't download a thing
        self.assertEqual(self.murano_client.packages.download.call_count, 2)

        # check that old directories were not deleted
        # we did not call cleanup and did not release the locks
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version, first_id)))

        # check that new directories got created correctly
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn)))
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version)))
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version, second_id)))
        self.assertTrue(os.path.isfile(os.path.join(
            self.location, fqn, package.version, second_id, 'manifest.yaml')))

        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version)))
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version, second_id)))

        # changing id, new package would be downloaded.
        package.id = third_id
        self.loader._package_cache = {}
        self.loader._class_cache = {}

        # release all the locks
        self.loader.cleanup()
        self.loader.load_class_package(fqn, spec)

        # check that we didn't download a thing
        self.assertEqual(self.murano_client.packages.download.call_count, 3)

        # check that old directories were *deleted*
        self.assertFalse(os.path.isdir(os.path.join(
            self.location, fqn, package.version, first_id)))
        self.assertFalse(os.path.isdir(os.path.join(
            self.location, fqn, package.version, second_id)))

        # check that new directories got created correctly
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version, third_id)))
        self.assertTrue(os.path.isfile(os.path.join(
            self.location, fqn, package.version, third_id, 'manifest.yaml')))


class TestCombinedPackageLoader(base.MuranoTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCombinedPackageLoader, cls).setUpClass()

        location = os.path.dirname(__file__)
        CONF.set_override('load_packages_from', [location], 'engine',
                          enforce_type=True)
        cls.execution_session = mock.MagicMock()
        cls.loader = package_loader.CombinedPackageLoader(
            cls.execution_session)
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
