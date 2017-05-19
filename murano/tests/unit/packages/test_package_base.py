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
import semantic_version
import shutil
import string
import tempfile

from murano.packages import exceptions
from murano.packages import package_base
import murano.tests.unit.base as test_base


class TestPackageBase(test_base.MuranoTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestPackageBase, cls).setUpClass()
        package_base.PackageBase.__abstractmethods__ = set()
        cls.source_directory = tempfile.mkdtemp(dir=tempfile.tempdir)
        cls.version = semantic_version.Version.coerce('1.2.3')
        cls.mock_manifest = {
            'Name': 'mock_display_name',
            'FullName': 'mock_full_name',
            'Type': 'Application',
            'Version': '1.2.3',
            'Description': 'test_description',
            'Author': 'test_author',
            'Supplier': 'test_supplier',
            'Tags': ['tag1', 'tag2', 'tag3'],
            'Logo': None
        }
        cls.package_base = package_base.PackageBase('test_format',
                                                    'test_runtime_version',
                                                    cls.source_directory,
                                                    cls.mock_manifest)

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls.source_directory):
            shutil.rmtree(cls.source_directory)

    def test_create_package_base_without_full_name(self):
        with self.assertRaisesRegex(exceptions.PackageFormatError,
                                    'FullName is not specified'):
            package_base.PackageBase('test_format',
                                     'test_runtime_version',
                                     'test_source_directory',
                                     manifest={'FullName': None})

    def test_create_package_base_with_invalid_full_name(self):
        full_names = ['.invalid_name_1', 'invalid..name..2', 'invalid name 3']
        for full_name in full_names:
            expected_error_message = 'Invalid FullName {0}'.format(full_name)
            with self.assertRaisesRegex(exceptions.PackageFormatError,
                                        expected_error_message):
                package_base.PackageBase('test_format',
                                         'test_runtime_version',
                                         'test_source_directory',
                                         manifest={'FullName': full_name})

    def test_create_package_base_with_invalid_type(self):
        package_type = 'Invalid'
        with self.assertRaisesRegex(exceptions.PackageFormatError,
                                    'Invalid package Type {0}'
                                    .format(package_type)):
            package_base.PackageBase('test_format',
                                     'test_runtime_version',
                                     'test_source_directory',
                                     manifest={'FullName': 'mock_full_name',
                                               'Type': package_type})

    def test_requirements_negative(self):
        with self.assertRaisesRegex(NotImplementedError, None):
            self.package_base.requirements

    def test_classes_negative(self):
        with self.assertRaisesRegex(NotImplementedError, None):
            self.package_base.classes

    def test_get_class_negative(self):
        with self.assertRaisesRegex(NotImplementedError, None):
            self.package_base.get_class(None)

    def test_ui_negative(self):
        with self.assertRaisesRegex(NotImplementedError, None):
            self.package_base.ui

    def test_full_name(self):
        self.assertEqual(self.mock_manifest['FullName'],
                         self.package_base.full_name)

    def test_source_directory(self):
        self.assertEqual(self.source_directory,
                         self.package_base.source_directory)

    def test_version(self):
        self.assertEqual(self.version,
                         self.package_base.version)

    def test_package_type(self):
        self.assertEqual(self.mock_manifest['Type'],
                         self.package_base.package_type)

    def test_display_name(self):
        self.assertEqual(self.mock_manifest['Name'],
                         self.package_base.display_name)

    def test_description(self):
        self.assertEqual(self.mock_manifest['Description'],
                         self.package_base.description)

    def test_author(self):
        self.assertEqual(self.mock_manifest['Author'],
                         self.package_base.author)

    def test_supplier(self):
        self.assertEqual(self.mock_manifest['Supplier'],
                         self.package_base.supplier)

    def test_tags(self):
        self.assertEqual(self.mock_manifest['Tags'],
                         self.package_base.tags)

    def test_logo_without_file_name(self):
        self.assertIsNone(self.package_base.logo)

    def test_logo_with_invalid_logo_path(self):
        expected_error_message = 'Unable to load logo'
        self.package_base._logo = ''.join(random.choice(string.ascii_letters)
                                          for _ in range(10))
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_message):
            self.package_base.logo
        self.package_base._logo = self.mock_manifest['Logo']

    @mock.patch('murano.packages.package_base.imghdr',
                what=mock.MagicMock(return_value='xyz'))
    def test_load_image_with_invalid_extension(self, mock_imghdr):
        expected_error_message = 'Unsupported Format.'
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_message):
            self.package_base._load_image('logo.xyz', 'logo.xyz', 'logo')
            full_path = os.path.join(self.package_base._source_directory,
                                     'logo.xyz')
            mock_imghdr.what.assert_called_once_with(full_path)

    @mock.patch('murano.packages.package_base.imghdr',
                what=mock.MagicMock(return_value='png'))
    @mock.patch('murano.packages.package_base.os')
    def test_load_image_with_oversized_image(self, mock_os, mock_imghdr):
        mock_os.stat.return_value = mock.MagicMock(st_size=5000 * 1024)
        mock_os.isfile = mock.MagicMock(return_value=True)
        expected_error_message = 'Max allowed size is {0}'.format(500 * 1024)
        with self.assertRaisesRegex(exceptions.PackageLoadError,
                                    expected_error_message):
            self.package_base._load_image('logo.xyz', 'logo.xyz', 'logo')

    def test_meta(self):
        self.assertIsNone(self.package_base.meta)

    def test_get_resource(self):
        test_name = 'test_resource_name'
        expected_dir = os.path.join(self.source_directory, 'Resources',
                                    test_name)
        self.assertEqual(expected_dir, self.package_base.get_resource(
            test_name))
