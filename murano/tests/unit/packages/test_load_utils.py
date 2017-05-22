# Copyright (c) 2016 AT&T Corp
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

import mock
import os
import random
import shutil
import string
import tempfile
import yaml
import zipfile

from murano.packages import exceptions
from murano.packages import load_utils
import murano.tests.unit.base as test_base


class TestLoadUtils(test_base.MuranoTestCase):

    def setUp(cls):
        super(TestLoadUtils, cls).setUp()
        cls.temp_directories = []
        cls.temp_files = []

    def _create_temp_dir(self):
        temp_directory = tempfile.mkdtemp()
        self.temp_directories.append(temp_directory)
        return temp_directory

    def _create_temp_file(self):
        temp_file = tempfile.NamedTemporaryFile(delete=True)
        self.temp_files.append(temp_file)
        return temp_file

    def _create_temp_zip_file(self, zip_path, manifest_path,
                              arcname='manifest.yaml'):
        zip_ = zipfile.ZipFile(zip_path, 'w')
        zip_.write(manifest_path, arcname=arcname)
        zip_.close()
        self.temp_files.append(zip_)
        return zip_

    def tearDown(cls):
        super(TestLoadUtils, cls).tearDown()
        for directory in cls.temp_directories:
            if os.path.isdir(directory):
                shutil.rmtree(directory)
        for file in cls.temp_files:
            if isinstance(file, zipfile.ZipFile):
                if zipfile.is_zipfile(file.filename):
                    os.remove(file)
            else:
                if os.path.isfile(file.name):
                    os.remove(file.name)

    def _test_load_from_file(self, target_dir=None, drop_dir=True):
        manifest_file_contents = dict(
            Format='MuranoPL/1.1',
            FullName='test_full_name',
            Type='Application',
            Description='test_description',
            Author='test_author',
            Supplier='test_supplier',
            Tags=[]
        )
        test_directory = self._create_temp_dir()
        manifest_path = os.path.join(test_directory, 'manifest.yaml')
        zip_path = os.path.join(test_directory, 'test_zip_load_utils.zip')

        with open(manifest_path, 'w') as manifest_file:
            yaml.dump(manifest_file_contents, manifest_file,
                      default_flow_style=True)
            self._create_temp_zip_file(zip_path, manifest_path)

        with load_utils.load_from_file(archive_path=zip_path,
                                       target_dir=target_dir,
                                       drop_dir=drop_dir) as plugin:
            self.assertEqual('MuranoPL', plugin.format_name)
            self.assertEqual('1.1.0', str(plugin.runtime_version))
            self.assertEqual(manifest_file_contents['FullName'],
                             plugin.full_name)
            self.assertEqual(manifest_file_contents['Description'],
                             plugin.description)
            self.assertEqual(manifest_file_contents['Author'],
                             plugin.author)
            self.assertEqual(manifest_file_contents['Supplier'],
                             plugin.supplier)
            self.assertEqual(manifest_file_contents['Tags'],
                             plugin.tags)

    def test_load_from_file(self):
        self._test_load_from_file(target_dir=None, drop_dir=True)

    def test_load_from_file_with_custom_target_directory(self):
        target_dir = self._create_temp_dir()
        self._test_load_from_file(target_dir=target_dir, drop_dir=True)

    @mock.patch('murano.packages.load_utils.get_plugin_loader')
    def test_load_from_file_with_invalid_handler(self, mock_plugin_loader):
        mock_plugin_loader().get_package_handler = mock.MagicMock(
            return_value=None)
        test_format = 'Invalid Format'
        manifest_file_contents = dict(
            Format=test_format,
            FullName='test_full_name',
            Type='Application',
            Description='test_description',
            Author='test_author',
            Supplier='test_supplier',
            Tags=[]
        )
        test_directory = self._create_temp_dir()
        target_dir = self._create_temp_dir()
        manifest_path = os.path.join(test_directory, 'manifest.yaml')
        zip_path = os.path.join(test_directory, 'test_zip_load_utils.zip')

        with open(manifest_path, 'w') as manifest_file:
            yaml.dump(manifest_file_contents, manifest_file,
                      default_flow_style=True)
            self._create_temp_zip_file(zip_path, manifest_path)

        expected_error_msg = "Unsupported format {0}".format(test_format)
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            with load_utils.load_from_file(archive_path=zip_path,
                                           target_dir=target_dir,
                                           drop_dir=True):
                pass
        mock_plugin_loader().get_package_handler.assert_called_once_with(
            test_format)

    def test_load_from_file_with_invalid_archive_path(self):
        expected_error_msg = "Unable to find package file"
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            with load_utils.load_from_file('invalid file path'):
                pass

    @mock.patch('murano.packages.load_utils.os')
    def test_load_from_file_with_nonempty_target_directory(self, mock_os):
        mock_os.listdir = mock.MagicMock(return_value=True)
        temp_file = self._create_temp_file()
        expected_error_msg = "Target directory is not empty"
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            this_dir = os.path.dirname(os.path.realpath(__file__))
            with load_utils.load_from_file(temp_file.name,
                                           target_dir=this_dir):
                pass

    def test_load_from_file_without_zip_file(self):
        temp_file = self._create_temp_file()
        expected_error_msg = "Uploaded file {0} is not a zip archive".\
                             format(temp_file.name)
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            with load_utils.load_from_file(temp_file.name):
                pass

    @mock.patch('murano.packages.load_utils.zipfile')
    def test_load_from_file_handle_value_error(self, mock_zipfile):
        test_error_msg = 'Random error message.'
        expected_error_msg = "Couldn't load package from file: {0}".\
                             format(test_error_msg)
        mock_zipfile.is_zipfile = mock.MagicMock(
            side_effect=ValueError(test_error_msg))
        temp_file = self._create_temp_file()
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            with load_utils.load_from_file(temp_file.name):
                pass
        mock_zipfile.is_zipfile.assert_called_once_with(
            temp_file.name)

    def test_load_from_dir_without_source_directory(self):
        expected_error_msg = 'Invalid package directory'
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            load_utils.load_from_dir('random_test_directory')

    def test_load_from_dir_with_invalid_source_directory(self):
        source_directory = self._create_temp_dir()
        expected_error_msg = 'Unable to find package manifest'
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            load_utils.load_from_dir(source_directory)

    @mock.patch('murano.packages.load_utils.os.path.isfile')
    def test_load_from_dir_open_file_negative(self, mock_isfile):
        mock_isfile.return_value = True
        source_directory = self._create_temp_dir()
        random_filename = ''.join(random.choice(string.ascii_lowercase)
                                  for i in range(20))
        expected_error_msg = 'Unable to load due to'
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_msg):
            load_utils.load_from_dir(source_directory,
                                     filename=random_filename)
