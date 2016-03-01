#    Copyright (c) 2014 Mirantis, Inc.
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

from tempest.lib import exceptions
from tempest.test import attr

from murano.tests.functional.api import base


class TestEnvironments(base.TestCase):

    @attr(type='smoke')
    def test_list_environments(self):
        resp, body = self.client.get_environments_list()

        self.assertIn('environments', body)
        self.assertEqual(resp.status, 200)

    @attr(type='smoke')
    def test_create_and_delete_environment(self):
        environments_list_start = self.client.get_environments_list()[1]

        resp, env = self.client.create_environment('test')
        self.environments.append(env)

        self.assertEqual(resp.status, 200)
        self.assertEqual('test', env['name'])

        environments_list = self.client.get_environments_list()[1]

        self.assertEqual(len(environments_list_start['environments']) + 1,
                         len(environments_list['environments']))

        self.client.delete_environment(env['id'])

        environments_list = self.client.get_environments_list()[1]

        self.assertEqual(len(environments_list_start['environments']),
                         len(environments_list['environments']))

        self.environments.pop(self.environments.index(env))

    @attr(type='smoke')
    def test_get_environment(self):
        env = self.create_environment('test')

        resp, environment = self.client.get_environment(env['id'])

        self.assertEqual(resp.status, 200)
        self.assertEqual(environment['name'], 'test')

    @attr(type='smoke')
    def test_update_environment(self):
        env = self.create_environment('test')

        resp, environment = self.client.update_environment(env['id'])

        self.assertEqual(resp.status, 200)
        self.assertEqual(environment['name'], 'changed-environment-name')

    @attr(type='negative')
    def test_update_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.update_environment,
                          None)

    @attr(type='negative')
    def test_delete_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_environment,
                          None)

    @attr(type='negative')
    def test_double_delete_environment(self):
        env = self.create_environment('test')

        self.client.delete_environment(env['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.delete_environment,
                          env['id'])

    @attr(type='negative')
    def test_get_deleted_environment(self):
        env = self.create_environment('test')

        self.client.delete_environment(env['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.get_environment,
                          env['id'])


class TestEnvironmentsTenantIsolation(base.NegativeTestCase):

    @attr(type='negative')
    def test_get_environment_from_another_tenant(self):
        env = self.create_environment('test')

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.get_environment, env['id'])

    @attr(type='negative')
    def test_update_environment_from_another_tenant(self):
        env = self.create_environment('test')

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.update_environment, env['id'])

    @attr(type='negative')
    def test_delete_environment_from_another_tenant(self):
        env = self.create_environment('test')

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.delete_environment, env['id'])
