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

import os
import yaml

from murano.packages import exceptions
import murano.packages.hot_package
import murano.packages.load_utils as load_utils
import murano.tests.unit.base as test_base


class TestHotPackage(test_base.MuranoTestCase):

    def _get_hot_package(self, source_directory):
        manifest = {
            'FullName': 'FullTestName',
            'Version': '1.0.0',
            'Type': 'Application',
            'Name': 'TestName',
            'Description': 'TestDescription',
            'Author': 'TestAuthor',
            'Supplier': 'TestSupplier',
            'Logo:': 'TestLogo',
            'Tags': ['Tag1', 'Tag2']
        }
        return murano.packages.hot_package.HotPackage(
            None, None, source_directory=source_directory,
            manifest=manifest
        )

    @classmethod
    def setUpClass(cls):
        super(TestHotPackage, cls).setUpClass()
        this_dir = os.path.dirname(os.path.realpath(__file__))
        cls.test_dirs = [
            os.path.join(this_dir, 'test.hot.1'),
            os.path.join(this_dir, 'test.hot.2'),
            os.path.join(this_dir, 'test.hot.3')
        ]

        manifest_path = os.path.join(cls.test_dirs[0], 'template.yaml')
        cls.manifest = {}
        with open(manifest_path) as manifest_file:
            for key, value in yaml.safe_load(manifest_file).items():
                cls.manifest[key] = value

        properties_manifest_path = os.path.join(cls.test_dirs[0],
                                                'properties_manifest.yaml')
        cls.properties_manifest = {}
        with open(properties_manifest_path) as manifest_file:
            for key, value in yaml.safe_load(manifest_file).items():
                cls.properties_manifest[key] = value

    def test_heat_files_generated(self):
        package_dir = os.path.abspath(
            os.path.join(__file__,
                         '../../test_packages/test.hot.v1.app_with_files')
        )
        load_utils.load_from_dir(package_dir)

        files = murano.packages.hot_package.HotPackage._translate_files(
            package_dir)
        expected_result = {
            "testHeatFile",
            "middle_file/testHeatFile",
            "middle_file/inner_file/testHeatFile",
            "middle_file/inner_file2/testHeatFile"
        }
        msg = "hot files were not generated correctly"
        self.assertSetEqual(expected_result, set(files), msg)

    def test_heat_files_generated_empty(self):
        package_dir = os.path.abspath(
            os.path.join(__file__,
                         '../../test_packages/test.hot.v1.app')
        )
        load_utils.load_from_dir(package_dir)

        files = murano.packages.hot_package.HotPackage \
            ._translate_files(package_dir)
        msg = "heat files were not generated correctly. Expected empty list"
        self.assertEqual([], files, msg)

    def test_build_properties(self):
        result = murano.packages.hot_package.HotPackage._build_properties(
            self.properties_manifest,
            validate_hot_parameters=True)

        self.assertIn('templateParameters', result)
        params = result['templateParameters']
        self.assertEqual(6, len(params['Contract']))

        param1 = params['Contract']['param1']
        param2 = params['Contract']['param2']
        param3 = params['Contract']['param3']
        param4 = params['Contract']['param4']
        param5 = params['Contract']['param5']
        param6 = params['Contract']['param6']

        self.assertEqual("$.bool().check($ in list(True, False))", param1.expr)
        self.assertEqual("$.string().check($ in list('bar'))."
                         "check(len($) <= 50).check(len($) >= 0)."
                         "check(matches($, '[A-Za-z0-9]'))", param2.expr)
        self.assertEqual("$.int().check($ in list(0, 1, 2, 3, 4))"
                         ".check(len($) >= 0 and len($) <= 5)."
                         "check($ >= 0 and $ <= 4)", param3.expr)
        self.assertEqual("$.int().check($ >= -1000).check($ <= "
                         "1000)", param4.expr)
        self.assertEqual("$.string()", param5.expr)
        self.assertEqual("$.string()", param6.expr)

        result = murano.packages.hot_package.HotPackage._build_properties(
            self.properties_manifest,
            validate_hot_parameters=False)
        expected_result = {
            'Contract': {},
            'Default': {},
            'Usage': 'In'
        }
        self.assertEqual(expected_result, result['templateParameters'])

    def test_translate_param_to_contract_with_inappropriate_value(self):
        self.assertRaisesRegex(
            ValueError,
            'Unsupported parameter type',
            murano.packages.hot_package.HotPackage.
            _translate_param_to_contract,
            {'type': 'Inappropriate value'}
        )

    def test_get_class_name(self):
        hot_package = self._get_hot_package(self.test_dirs[0])
        translated_class, _ = hot_package.get_class(hot_package.full_name)
        self.assertIsNotNone(translated_class)
        self.assertEqual(translated_class, hot_package._translated_class)

    def test_get_class_name_with_invalid_template_name(self):
        hot_package = self._get_hot_package(self.test_dirs[0])
        self.assertRaisesRegex(
            exceptions.PackageClassLoadError,
            'Class not defined in this package',
            hot_package.get_class,
            None)

    def test_get_class_name_with_invalid_template_format(self):
        hot_package = self._get_hot_package(self.test_dirs[1])
        self.assertRaisesRegex(
            exceptions.PackageFormatError,
            'Not a HOT template',
            hot_package.get_class,
            hot_package.full_name)

    def test_translate_ui(self):
        hot_package = self._get_hot_package(self.test_dirs[0])
        yaml = hot_package._translate_ui()
        self.assertIsNotNone(yaml)
        expected_application = '''
            "Application":
              "?":
                "classVersion": "1.0.0"
                "package": "FullTestName"
                "type": "FullTestName"
              "name": !yaql "$.group0.name"
              "templateParameters":
                "bar": !yaql "$.group1.bar"
                "baz": !yaql "$.group1.baz"
                "foo": !yaql "$.group1.foo"
        '''
        self.assertIn(expected_application.replace(' ', '').replace('\n', ''),
                      yaml.replace(' ', '').replace('\n', ''))

    def test_translate_ui_with_nonexistent_template(self):
        hot_package = self._get_hot_package(self.test_dirs[2])
        self.assertRaisesRegex(
            exceptions.PackageClassLoadError,
            'File with class definition not found',
            hot_package._translate_ui)

    def test_translate_class_with_nonexistent_template(self):
        hot_package = self._get_hot_package(self.test_dirs[2])
        self.assertRaisesRegex(
            exceptions.PackageClassLoadError,
            'File with class definition not found',
            hot_package._translate_class)
