# Copyright (c) 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from murano.tests.functional.cli import muranoclient


class SimpleReadOnlyMuranoClientTest(muranoclient.ClientTestBase):
    """Basic, read-only tests for Murano CLI client.

    Basic smoke test for the Murano CLI commands which do not require
    creating or modifying murano objects.
    """

    @classmethod
    def setUpClass(cls):
        super(SimpleReadOnlyMuranoClientTest, cls).setUpClass()

    def test_environment_list(self):
        environments = self.parser.listing(self.murano('environment-list'))

        self.assertTableStruct(environments,
                               ['ID', 'Name', 'Created', 'Updated'])

    def test_package_list(self):
        packages = self.parser.listing(self.murano('package-list'))

        self.assertTableStruct(packages,
                               ['ID', 'Name', 'FQN', 'Author', 'Is Public'])

    def test_category_list(self):
        self.murano('category-list')
