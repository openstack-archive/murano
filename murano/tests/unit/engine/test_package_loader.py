# Copyright 2016 AT&T Corp
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
from muranoclient.common import exceptions as muranoclient_exc
import os
import shutil
import tempfile

import mock
import semantic_version
import testtools

from murano.dsl import exceptions as dsl_exceptions
from murano.dsl import murano_package as dsl_package
from murano.engine import package_loader
from murano.packages import exceptions as pkg_exc
from murano.tests.unit import base
from murano.tests.unit import utils


class TestPackageCache(base.MuranoTestCase):

    def setUp(self):
        super(TestPackageCache, self).setUp()

        self.location = tempfile.mkdtemp()
        self.override_config('enable_packages_cache', True, 'engine')
        self.override_config('packages_cache', self.location, 'engine')

        self._patch_loader_client()
        self.loader = package_loader.ApiPackageLoader(None)

    def tearDown(self):
        shutil.rmtree(self.location, ignore_errors=True)
        super(TestPackageCache, self).tearDown()

    def _patch_loader_client(self):
        self.murano_client_patcher = mock.patch(
            'murano.engine.package_loader.ApiPackageLoader.client')
        self.murano_client_patcher.start()
        self.murano_client = package_loader.ApiPackageLoader.client

    def _unpatch_loader_client(self):
        self.murano_client_patcher.stop()

    @mock.patch('murano.engine.package_loader.auth_utils')
    @mock.patch('murano.engine.package_loader.versionutils')
    def test_client_property(self, mock_versionutils, mock_auth_utils):
        self._unpatch_loader_client()
        session = mock_auth_utils.get_client_session()
        session_params = mock_auth_utils.get_session_client_parameters
        session.auth.get_token.return_value = 'test_token'
        session.get_endpoint.return_value = 'test_endpoint/v3'
        session_params.return_value = {'endpoint': 'test_endpoint/v3'}

        self.override_config('packages_service', 'glance', group='engine')

        client = self.loader.client

        mock_versionutils.report_deprecated_feature.assert_called_once_with(
            package_loader.LOG,
            "'glance' packages_service option has been renamed "
            "to 'glare', please update your configuration")

        self.assertIsNotNone(client)
        self.assertIsNotNone(self.loader._glare_client)

        # Test whether client is initialized using different CONF.
        self.override_config('packages_service', 'test_service',
                             group='engine')

        client = self.loader.client

        self.assertIsNotNone(client)

    def test_import_fixations_table(self):
        test_fixations = {
            'test_package_1': [semantic_version.Version('1.1.0'),
                               semantic_version.Version('1.1.0')],
            'test_package_2': [semantic_version.Version('2.1.0'),
                               semantic_version.Version('2.4.3')]
        }
        expected = collections.defaultdict(set)
        expected['test_package_1'] = set([semantic_version.Version('1.1.0')])
        expected['test_package_2'] = set([semantic_version.Version('2.1.0'),
                                          semantic_version.Version('2.4.3')])

        self.loader.import_fixation_table(test_fixations)
        self.assertEqual(expected, self.loader._fixations)

    def test_register_package(self):
        test_version = semantic_version.Version('1.1.0')
        package = mock.MagicMock()
        package.name = 'test_package_name'
        package.version = test_version
        package.classes = ['test_class_1', 'test_class_2']

        self.loader.register_package(package)
        self.assertEqual(
            package,
            self.loader._package_cache['test_package_name'][test_version])
        for class_name in package.classes:
            self.assertEqual(
                package,
                self.loader._class_cache[class_name][test_version])

    def test_load_package(self):
        test_version = semantic_version.Version('1.1.0')

        package = mock.MagicMock()
        package.name = 'test_package_name'
        package.version = test_version
        self.loader.import_fixation_table({package.name: [test_version]})
        self.loader.register_package(package)

        version_spec = semantic_version.Spec('>=1.0.0,<2.4.0')
        retrieved_pkg = self.loader.load_package(package.name, version_spec)
        self.assertEqual(retrieved_pkg, package)

    @testtools.skipIf(os.name == 'nt', "Doesn't work on Windows")
    @mock.patch('murano.engine.package_loader.ApiPackageLoader.'
                '_to_dsl_package')
    def test_load_package_with_get_definiton(self, mock_to_dsl_package):
        fqn = 'io.murano.apps.test_package'
        package = mock.MagicMock()
        package.id = 'test_package_id'
        package.name = 'test_package_name'
        package.fully_qualified_name = fqn
        package.version = '2.5.3'

        path, _ = utils.compose_package(
            'test_package', self.location, archive_dir=self.location,
            version=package.version)
        with open(path, 'rb') as f:
            package_data = f.read()

        self.murano_client.packages.filter = mock.MagicMock(
            return_value=[package])
        self.murano_client.packages.download = mock.MagicMock(
            return_value=package_data)
        mock_to_dsl_package.return_value = package

        spec = semantic_version.Spec('*')
        retrieved_pkg = self.loader.load_package(fqn, spec)
        self.assertEqual(retrieved_pkg, package)

        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn)))
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version)))
        self.assertTrue(os.path.isdir(os.path.join(
            self.location, fqn, package.version, package.id)))
        self.assertTrue(os.path.isfile(os.path.join(
            self.location, fqn, package.version, package.id, 'manifest.yaml')))
        self.murano_client.packages.download.assert_called_once_with(
            package.id)

        expected_fixations = collections.defaultdict(set)
        expected_fixations[fqn] = set(
            [semantic_version.Version(package.version)])
        self.assertEqual(expected_fixations, self.loader._fixations)
        self.loader.cleanup()

    def test_load_package_except_lookup_error(self):
        expected_error_msg = 'Package "test_package_name" is not found'
        invalid_specs = [semantic_version.Spec('>=1.1.1'),
                         semantic_version.Spec('<1.1.0'),
                         semantic_version.Spec('>=1.1.1,<1.1.0'),
                         semantic_version.Spec('==1.1.1')]

        fqn = 'io.murano.apps.test'
        test_version = semantic_version.Version('1.1.0')
        package = mock.MagicMock()
        package.name = fqn
        package.fully_qualified_name = fqn
        package.version = test_version
        self.loader.import_fixation_table({fqn: [test_version]})
        self.loader.register_package(package)

        with self.assertRaisesRegex(dsl_exceptions.NoPackageFound,
                                    expected_error_msg):
            for spec in invalid_specs:
                self.loader.load_package('test_package_name', spec)

    def test_load_class_package(self):
        fqn = 'io.murano.apps.test'
        package = mock.MagicMock()
        package.fully_qualified_name = fqn
        package.classes = ['test_class_1', 'test_class_2']
        self.loader.register_package(package)

        spec = semantic_version.Spec('*')
        for class_name in ['test_class_1', 'test_class_2']:
            retrieved_pkg = self.loader.load_class_package(class_name, spec)
            self.assertEqual(retrieved_pkg, package)

    @testtools.skipIf(os.name == 'nt', "Doesn't work on Windows")
    def test_load_class_package_with_get_definition(self):
        fqn = 'io.murano.apps.test'
        path, name = utils.compose_package(
            'test',
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

        # assert that we called download
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

    def test_load_class_package_except_lookup_error(self):
        invalid_specs = [semantic_version.Spec('>=1.1.1'),
                         semantic_version.Spec('<1.1.0'),
                         semantic_version.Spec('>=1.1.1,<1.1.0'),
                         semantic_version.Spec('==1.1.1')]

        fqn = 'io.murano.apps.test'
        test_version = semantic_version.Version('1.1.0')
        package = mock.MagicMock()
        package.name = fqn
        package.fully_qualified_name = fqn
        package.version = test_version
        package.classes = ['test_class_1', 'test_class_2']
        self.loader.import_fixation_table({fqn: [test_version]})
        self.loader.register_package(package)

        for class_ in package.classes:
            expected_error_msg = 'Package for class "{0}" is not found'\
                                 .format(class_)
            with self.assertRaisesRegex(dsl_exceptions.NoPackageForClassFound,
                                        expected_error_msg):
                for spec in invalid_specs:
                    self.loader.load_class_package(class_, spec)

    @mock.patch('murano.engine.package_loader.LOG')
    def test_get_definition_with_multiple_packages_returned(self, mock_log):
        self.loader._execution_session = mock.MagicMock()
        self.loader._execution_session.project_id = 'test_project_id'

        matching_pkg = mock.MagicMock(owner_id='test_project_id',
                                      is_public=False)
        public_pkg = mock.MagicMock(owner_id='another_test_project_id',
                                    is_public=True)
        other_pkg = mock.MagicMock(owner_id='another_test_project_id',
                                   is_public=False)

        # Test package with matching owner_id is returned, despite ordering.
        self.loader.client.packages.filter.return_value =\
            [public_pkg, matching_pkg, other_pkg]
        expected_pkg = matching_pkg
        retrieved_pkg = self.loader._get_definition({})
        self.assertEqual(expected_pkg, retrieved_pkg)

        # Test public package is returned, despite ordering.
        self.loader.client.packages.filter.return_value =\
            [other_pkg, public_pkg]
        expected_pkg = public_pkg
        retrieved_pkg = self.loader._get_definition({})
        self.assertEqual(expected_pkg, retrieved_pkg)

        # Test other package is returned.
        self.loader.client.packages.filter.return_value =\
            [other_pkg, other_pkg]
        expected_pkg = other_pkg
        retrieved_pkg = self.loader._get_definition({})
        self.assertEqual(expected_pkg, retrieved_pkg)

        mock_log.debug.assert_any_call(
            'Ambiguous package resolution: more than 1 package found for query'
            ' "{opts}", will resolve based on the ownership'
            .format(opts={'catalog': True}))

    @mock.patch('murano.engine.package_loader.LOG')
    def test_get_definition_except_lookup_error(self, mock_log):
        self.loader.client.packages.filter.return_value = []

        with self.assertRaisesRegex(LookupError, None):
            self.loader._get_definition({})

        mock_log.debug.assert_called_once_with(
            "There are no packages matching filter {opts}"
            .format(opts={'catalog': True}))
        mock_log.debug.reset_mock()

        self.loader.client.packages.filter.side_effect =\
            muranoclient_exc.HTTPException

        with self.assertRaisesRegex(LookupError, None):
            self.loader._get_definition({})

        mock_log.debug.assert_called_once_with(
            'Failed to get package definition from repository')

    @testtools.skipIf(os.name == 'nt', "Doesn't work on Windows")
    @mock.patch('murano.engine.package_loader.LOG')
    @mock.patch('murano.engine.package_loader.os')
    @mock.patch('murano.engine.package_loader.load_utils')
    def test_get_package_by_definition_except_package_load_error(
            self, mock_load_utils, mock_os, mock_log):
        # Test that the first instance of the exception is caught.
        temp_directory = tempfile.mkdtemp(prefix='test-package-loader-',
                                          dir=tempfile.tempdir)
        mock_os.path.isdir.return_value = True
        mock_os.path.join.return_value = temp_directory
        mock_load_utils.load_from_dir.side_effect = pkg_exc.PackageLoadError

        fqn = 'io.murano.apps.test'
        path, _ = utils.compose_package(
            'test', self.location, archive_dir=self.location)
        with open(path, 'rb') as f:
            package_data = f.read()

        package = mock.MagicMock()
        package.fully_qualified_name = fqn
        package.id = '123'
        package.version = '0.0.1'

        self.murano_client.packages.download = mock.MagicMock(
            return_value=package_data)

        self.loader._get_package_by_definition(package)

        mock_log.exception.assert_called_once_with(
            'Unable to load package from cache. Clean-up.')
        mock_log.exception.reset_mock()

        # Test that the second instance of the exception is caught.
        mock_os.path.isdir.return_value = [False, True]

        self.loader._get_package_by_definition(package)

        mock_log.exception.assert_called_once_with(
            'Unable to load package from cache. Clean-up.')
        os.remove(temp_directory)

    @testtools.skipIf(os.name == 'nt', "Doesn't work on Windows")
    def test_get_package_by_definition_except_http_exception(self):
        fqn = 'io.murano.apps.test'
        path, _ = utils.compose_package(
            'test', self.location, archive_dir=self.location)

        package = mock.MagicMock()
        package.fully_qualified_name = fqn
        package.id = '123'
        package.version = '0.0.1'

        self.murano_client.packages.download.side_effect =\
            muranoclient_exc.HTTPException

        expected_error_msg = 'Error loading package id {0}:'.format(package.id)
        with self.assertRaisesRegex(pkg_exc.PackageLoadError,
                                    expected_error_msg):
            self.loader._get_package_by_definition(package)

    @testtools.skipIf(os.name == 'nt', "Doesn't work on Windows")
    @mock.patch('murano.engine.package_loader.LOG')
    @mock.patch('murano.engine.package_loader.tempfile')
    def test_get_package_by_definition_except_io_error(self, mock_tempfile,
                                                       mock_log):
        fqn = 'io.murano.apps.test'
        path, _ = utils.compose_package(
            'test', self.location, archive_dir=self.location)
        with open(path, 'rb') as f:
            package_data = f.read()

        package = mock.MagicMock()
        package.fully_qualified_name = fqn
        package.id = '123'
        package.version = '0.0.1'

        self.murano_client.packages.download = mock.MagicMock(
            return_value=package_data)
        mock_package_file = mock.MagicMock(
            write=mock.MagicMock(side_effect=IOError))
        mock_package_file.configure_mock(name='test_package_file')
        mock_tempfile.NamedTemporaryFile().__enter__.return_value =\
            mock_package_file

        expected_error_msg = 'Unable to extract package data for {0}'\
                             .format(package.id)
        with self.assertRaisesRegex(pkg_exc.PackageLoadError,
                                    expected_error_msg):
            self.loader._get_package_by_definition(package)

    def test_try_cleanup_cache_with_null_package_directory(self):
        # Test null package directory causes early return.
        result = self.loader.try_cleanup_cache(None, None)
        self.assertIsNone(result)

    @mock.patch('murano.engine.package_loader.shutil')
    @mock.patch('murano.engine.package_loader.m_utils')
    @mock.patch('murano.engine.package_loader.usage_mem_locks')
    @mock.patch('murano.engine.package_loader.LOG')
    @mock.patch('murano.engine.package_loader.os')
    def test_try_cleanup_cache_except_os_error(self, mock_os, mock_log,
                                               mock_usage_mem_locks, *args):
        # Test first instance of OSError is handled.
        mock_os.listdir.side_effect = OSError

        result = self.loader.try_cleanup_cache(None, None)
        self.assertIsNone(result)

        # Test second instance of OSError is handled.
        mock_os.reset_mock()
        mock_os.listdir.return_value = {'1', '2'}
        mock_os.listdir.side_effect = None
        mock_os.remove.side_effect = OSError
        mock_usage_mem_locks.__getitem__().write_lock().__enter__.\
            return_value = True

        result = self.loader.try_cleanup_cache('test_package_directory', None)
        self.assertIsNone(result)

        self.assertIn("Couldn't delete lock file:",
                      str(mock_log.warning.mock_calls[0]))


class TestCombinedPackageLoader(base.MuranoTestCase):

    def setUp(self):
        super(TestCombinedPackageLoader, self).setUp()

        location = os.path.dirname(__file__)
        self.override_config('load_packages_from', [location], 'engine')
        self.execution_session = mock.MagicMock()
        self.loader = package_loader.CombinedPackageLoader(
            self.execution_session)
        self._patch_api_loader()

        self.local_pkg_name = 'io.murano.test.MyTest'
        self.api_pkg_name = 'test.mpl.v1.app.Thing'

    def _patch_api_loader(self):
        self.api_loader_patcher = mock.patch.object(
            self.loader, 'api_loader', return_value=mock.MagicMock())
        self.api_loader_patcher.start()

    def _unpatch_api_loader(self):
        self.api_loader_patcher.stop()

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

        self.loader.api_loader.load_package.assert_called_with(
            self.api_pkg_name, spec)

    def test_get_package_api_loader(self):
        spec = semantic_version.Spec('*')
        self.loader.load_class_package(self.api_pkg_name, spec)

        self.loader.api_loader.load_class_package.assert_called_with(
            self.api_pkg_name, spec)

    def test_register_package(self):
        test_package = mock.MagicMock()
        self.loader.register_package(test_package)
        self.loader.api_loader.register_package.assert_called_once_with(
            test_package)

    def test_import_fixation_table(self):
        self.loader.directory_loaders = [
            mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        ]
        test_fixations = {
            'test_package_1': [semantic_version.Version('1.1.0')],
            'test_package_2': [semantic_version.Version('2.1.0'),
                               semantic_version.Version('2.4.3')]
        }
        self.loader.import_fixation_table(test_fixations)
        self.loader.api_loader.import_fixation_table.assert_called_once_with(
            test_fixations)
        for loader in self.loader.directory_loaders:
            loader.import_fixation_table.assert_called_once_with(
                test_fixations)

    def test_compact_fixation_table(self):
        self.loader.directory_loaders = [
            mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        ]
        self.loader.compact_fixation_table()
        self.loader.api_loader.compact_fixation_table.assert_called_once_with()
        for loader in self.loader.directory_loaders:
            loader.compact_fixation_table.assert_called_once_with()

    def test_export_fixation_table(self):
        self._unpatch_api_loader()

        test_fixations = {
            'test_package_1': [semantic_version.Version('1.1.1')],
            'test_package_2': [semantic_version.Version('2.2.2'),
                               semantic_version.Version('3.3.3')]
        }
        self.loader.api_loader.import_fixation_table(test_fixations)

        expected_table = {'test_package_1': ['1.1.1'],
                          'test_package_2': ['2.2.2', '3.3.3']}
        table = self.loader.export_fixation_table()

        self.assertEqual(sorted(expected_table.items()),
                         sorted(table.items()))

        test_fixations = {
            'test_package_1': [semantic_version.Version('4.4.4')],
            'test_package_2': [semantic_version.Version('5.5.5'),
                               semantic_version.Version('6.6.6')],
            'test_package_3': [semantic_version.Version('7.7.7')]
        }
        self.loader.directory_loaders[0].import_fixation_table(test_fixations)

        expected_table = {'test_package_1': ['1.1.1', '4.4.4'],
                          'test_package_2': ['2.2.2', '3.3.3', '5.5.5',
                                             '6.6.6'],
                          'test_package_3': ['7.7.7']}
        table = self.loader.export_fixation_table()
        for key, value in table.items():
            table[key] = sorted(value)

        self.assertEqual(sorted(expected_table.items()),
                         sorted(table.items()))
