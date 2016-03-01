#    Copyright (c) 2015 Telefonica I+D.
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


class TestEnvTemplate(base.TestCase):

    @attr(type='smoke')
    def test_list_env_templates(self):
        """Check getting the list of environment templates."""
        resp, body = self.client.get_env_templates_list()

        self.assertIn('templates', body)
        self.assertEqual(resp.status, 200)

    @attr(type='smoke')
    def test_create_and_delete_env_template(self):
        """It checks the creation and deletion of an enviroment template."""
        env_templates_list_start = self.client.get_env_templates_list()[1]

        resp, env_template = self.client.create_env_template('test_env_temp')
        self.env_templates.append(env_template)

        self.assertEqual(resp.status, 200)
        self.assertEqual('test_env_temp', env_template['name'])

        env_templates_list = self.client.get_env_templates_list()[1]

        self.assertEqual(len(env_templates_list_start['templates']) + 1,
                         len(env_templates_list['templates']))

        self.client.delete_env_template(env_template['id'])

        env_templates_list = self.client.get_env_templates_list()[1]

        self.assertEqual(len(env_templates_list_start['templates']),
                         len(env_templates_list['templates']))

        self.env_templates.pop(self.env_templates.index(env_template))

    @attr(type='smoke')
    def test_get_env_template(self):
        """Check getting information about an environment template."""
        resp, env_template = self.client.create_env_template('test_env_temp')

        resp, env_obtained_template =\
            self.client.get_env_template(env_template['id'])

        self.assertEqual(resp.status, 200)
        self.assertEqual(env_obtained_template['name'], 'test_env_temp')
        self.client.delete_env_template(env_template['id'])

    @attr(type='smoke')
    def test_create_env_template_with_apps(self):
        """Check the creation of an environment template with applications."""
        resp, env_template = \
            self.client.create_env_template_with_apps('test_env_temp')
        self.assertEqual(resp.status, 200)
        resp, apps_template = \
            self.client.get_apps_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(apps_template), 1)
        self.client.delete_env_template(env_template['id'])

    @attr(type='smoke')
    def test_create_app_in_env_template(self):
        """Check the creationg of applications in an environment template."""
        resp, env_template = self.client.create_env_template('test_env_temp')
        resp, apps = self.client.get_apps_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(apps), 0)

        resp, apps = self.client.create_app_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        resp, apps = self.client.get_apps_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(apps), 1)

        self.client.delete_env_template(env_template['id'])

    @attr(type='smoke')
    def test_delete_app_in_env_template(self):
        """Check the deletion of applications in an environmente template."""
        resp, env_template = self.client.create_env_template('test_env_temp')

        resp, apps = self.client.create_app_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        resp, apps = self.client.get_apps_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(apps), 1)
        resp = self.client.delete_app_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        resp, apps = self.client.get_apps_in_env_template(env_template['id'])
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(apps), 0)

        self.client.delete_env_template(env_template['id'])

    @attr(type='smoke')
    def test_create_env_from_template(self):
        """Check the creation of an environment from a template."""
        resp, env_template = \
            self.client.create_env_template_with_apps('test_env_temp')
        self.assertEqual(resp.status, 200)

        resp, env = self.client.create_env_from_template(env_template['id'],
                                                         "env")
        self.assertEqual(resp.status, 200)

        self.client.delete_env_template(env_template['id'])
        self.client.delete_environment(env['environment_id'])

    @attr(type='negative')
    def test_delete_environment_with_wrong_env_id(self):
        """Check the deletion of an wrong environment template request."""
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_env_template,
                          None)

    @attr(type='negative')
    def test_create_environment_with_wrong_payload(self):
        """Check the deletion of an wrong environment template request."""
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_env_template,
                          '-+3')

    @attr(type='negative')
    def test_double_delete_env_template(self):
        """Check the deletion of an wrong environment template request."""
        resp, env_template = self.client.create_env_template('test_env_temp')

        self.client.delete_env_template(env_template['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.delete_env_template,
                          env_template['id'])

    @attr(type='negative')
    def test_get_deleted_env_template(self):
        """Check the deletion of an wrong environment template request."""
        resp, env_template = self.client.create_env_template('test_env_temp')

        self.client.delete_env_template(env_template['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.get_env_template,
                          env_template['id'])


class TestEnvTemplatesTenantIsolation(base.NegativeTestCase):

    @attr(type='negative')
    def test_get_env_template_from_another_tenant(self):
        """It tests getting information from an environment
        template from another user.
        """
        env_template = self.create_env_template('test_env_temp')

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.get_env_template, env_template['id'])

        self.client.delete_env_template(env_template['id'])

    @attr(type='negative')
    def test_delete_env_template_from_another_tenant(self):
        """It tests deleting information from an environment
        template from another user.
        """
        env_template = self.create_env_template('test_env_temp')

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.delete_env_template,
                          env_template['id'])
        self.client.delete_env_template(env_template['id'])
