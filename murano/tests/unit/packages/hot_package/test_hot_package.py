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

import murano.packages.hot_package
import murano.packages.load_utils as load_utils
import murano.tests.unit.base as test_base


class TestHotPackage(test_base.MuranoTestCase):
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
