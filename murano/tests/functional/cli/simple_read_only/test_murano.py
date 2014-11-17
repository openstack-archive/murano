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

import time
import uuid

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
        environments = self.listing('environment-list')

        self.assertTableStruct(environments,
                               ['ID', 'Name', 'Created', 'Updated'])

    def test_package_list(self):
        packages = self.listing('package-list')

        self.assertTableStruct(packages,
                               ['ID', 'Name', 'FQN', 'Author', 'Is Public'])

    def test_category_list(self):
        self.murano('category-list')

    def test_table_struct_of_environment_create(self):
        env_name = "gg" + uuid.uuid4().hex
        environment = self.listing('environment-create', params=env_name)

        self.assertTableStruct(environment,
                               ['ID', 'Name', 'Created', 'Updated'])

    def test_table_struct_of_environment_delete(self):
        env_name = "gg" + uuid.uuid4().hex
        environment = self.listing('environment-create', params=env_name)

        ID = self.get_value('ID', 'Name', env_name, environment)

        delete_env = self.listing('environment-delete', params=ID)

        self.assertTableStruct(delete_env,
                               ['ID', 'Name', 'Created', 'Updated'])


class EnvironmentMuranoClientTest(muranoclient.ClientTestBase):

    @classmethod
    def setUpClass(cls):
        super(EnvironmentMuranoClientTest, cls).setUpClass()

    def test_environment_create(self):
        env_name = "gg" + uuid.uuid4().hex
        environment = self.listing('environment-create', params=env_name)

        environment_list = self.listing('environment-list')

        self.assertIn(env_name, [env['Name'] for env in environment])
        self.assertIn(env_name, [env['Name'] for env in environment_list])

    def test_environment_delete(self):
        env_name = "gg" + uuid.uuid4().hex
        environments = self.listing('environment-create', params=env_name)

        ID = self.get_value('ID', 'Name', env_name, environments)

        self.listing('environment-delete', params=ID)

        start_time = time.time()
        while env_name in [env['Name']
                           for env in self.listing('environment-list')]:
            if start_time - time.time() > 60:
                self.fail("Environment is not deleted in 60 seconds")

    def test_environment_show(self):
        env_name = "gg" + uuid.uuid4().hex
        environment = self.listing('environment-create', params=env_name)

        ID = self.get_value('ID', 'Name', env_name, environment)

        created = self.get_value('Created', 'Name', env_name, environment)
        updated = self.get_value('Updated', 'Name', env_name, environment)

        show_env = self.listing('environment-show', params=ID)

        self.assertEqual(env_name, self.get_value('Value', 'Property', 'name',
                                                  show_env))
        self.assertEqual(created, self.get_value('Value', 'Property',
                                                 'created', show_env))
        self.assertEqual(updated, self.get_value('Value', 'Property',
                                                 'updated', show_env))

    def test_environment_rename(self):
        env_name = "gg" + uuid.uuid4().hex
        environment = self.listing('environment-create', params=env_name)

        ID = self.get_value('ID', 'Name', env_name, environment)

        new_name = "renamed" + uuid.uuid4().hex
        rename_env = self.listing('environment-rename',
                                  params='{id} {name}'.format(id=ID,
                                                              name=new_name))

        show_env = self.listing('environment-show', params=ID)

        self.assertEqual(new_name, self.get_value('Name', 'ID', ID,
                                                  rename_env))
        self.assertEqual(new_name, self.get_value('Value', 'Property', 'name',
                                                  show_env))
