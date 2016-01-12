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

from nose.plugins.attrib import attr as tag
from tempest.test import attr
from tempest_lib import exceptions

from murano.tests.functional.api import base


class TestEnvTemplate(base.TestCase):

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_list_empty_env_templates(self):
        """Check getting the list of environment templates."""
        resp, body = self.client.get_env_templates_list()

        self.assertEqual(0, len(body))
        self.assertEqual(200, resp.status)

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_create_and_delete_env_template(self):
        """It checks the creation and deletion of an enviroment template."""
        env_templates_list_start = self.client.get_env_templates_list()[1]

        resp, env_template = self.create_env_template('test_env_temp')
        self.env_templates.append(env_template)

        self.assertEqual(200, resp.status)
        self.assertFalse(env_template['is_public'])
        self.assertEqual('test_env_temp', env_template['name'])

        env_templates_list = self.client.get_env_templates_list()[1]

        self.assertEqual(len(env_templates_list_start) + 1,
                         len(env_templates_list))

        self.client.delete_env_template(env_template['id'])

        env_templates_list = self.client.get_env_templates_list()[1]

        self.assertEqual(len(env_templates_list_start),
                         len(env_templates_list))

        self.env_templates.pop(self.env_templates.index(env_template))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_get_env_template(self):
        """Check getting information about an environment template."""
        resp, env_template = self.create_env_template('test_env_temp')

        resp, env_obtained_template =\
            self.client.get_env_template(env_template['id'])

        self.assertEqual(200, resp.status)
        self.assertEqual('test_env_temp', env_obtained_template['name'])

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_create_env_template_with_apps(self):
        """Check the creation of an environment template with applications."""
        resp, env_template = \
            self.create_env_template_with_apps('test_env_temp')
        self.assertEqual(200, resp.status)
        resp, apps_template = \
            self.client.get_apps_in_env_template(env_template['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(apps_template))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_create_app_in_env_template(self):
        """Check the creationg of applications in an environment template."""
        resp, env_temp = self.create_env_template('test_env_temp')
        self.assertEqual(200, resp.status)

        resp, apps = self.client.get_apps_in_env_template(env_temp['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(apps))

        resp, apps = self.client.create_app_in_env_template(env_temp['id'])
        self.assertEqual(200, resp.status)
        resp, apps = self.client.get_apps_in_env_template(env_temp['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(apps))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_delete_app_in_env_template(self):
        """Check the deletion of applications in an environmente template."""
        resp, env_temp = self.create_env_template_with_apps('test_env_temp')
        self.assertEqual(200, resp.status)
        resp, apps = self.client.get_apps_in_env_template(env_temp['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(apps))
        resp = self.client.delete_app_in_env_template(env_temp['id'])
        self.assertEqual(200, resp.status)
        resp, apps = self.client.get_apps_in_env_template(env_temp['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(apps))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_create_public_env_template(self):
        """Check the creation of a public environment template."""
        resp, env_temp = self.create_public_env_template('test_env_temp')
        self.assertEqual(200, resp.status)
        resp, env = self.client.get_env_template(env_temp['id'])
        self.assertEqual(200, resp.status)
        self.assertTrue(env['is_public'])

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_clone_env_template(self):
        """Check the creation of a public environment template."""
        resp, env_template = self.\
            create_public_env_template('test_env_temp')
        self.assertEqual(200, resp.status)
        resp, cloned_templ = self.clone_env_template(env_template['id'],
                                                     'cloned_template')
        self.assertEqual(200, resp.status)
        self.assertEqual('cloned_template', cloned_templ['name'])

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_clone_env_template_private(self):
        """Check the creation of a public environment template."""
        resp, env_template = self.\
            create_env_template('test_env_temp')
        self.assertEqual(200, resp.status)
        self.assertRaises(exceptions.Forbidden,
                          self.clone_env_template,
                          env_template['id'], 'cloned_template')

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_get_public_env_templates(self):
        """Check the deletion of applications in an environmente template."""
        resp, public_env_template = \
            self.create_public_env_template('public_test_env_temp')
        self.assertEqual(200, resp.status)
        self.assertTrue(public_env_template['is_public'])
        resp, private_env_template = \
            self.create_env_template('private_test_env_temp')
        self.assertEqual(200, resp.status)
        self.assertFalse(private_env_template['is_public'])
        resp, public_envs = self.client.get_public_env_templates_list()
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(public_envs))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_get_private_env_templates(self):
        """Check the deletion of applications in an environmente template."""
        resp, public_env_template = \
            self.create_public_env_template('public_test_env_temp')
        self.assertEqual(200, resp.status)
        self.assertTrue(public_env_template['is_public'])
        resp, private_env_template = \
            self.create_env_template('private_test_env_temp')
        self.assertEqual(200, resp.status)
        self.assertFalse(private_env_template['is_public'])
        resp, private_envs = self.client.get_private_env_templates_list()
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(private_envs))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_get_env_templates(self):
        """Check the deletion of applications in an environmente template."""
        resp, public_env_template = \
            self.create_public_env_template('public_test_env_temp')
        self.assertEqual(200, resp.status)
        self.assertTrue(public_env_template['is_public'])
        resp, private_env_template = \
            self.create_env_template('private_test_env_temp')
        self.assertEqual(200, resp.status)
        self.assertFalse(private_env_template['is_public'])
        resp, envs_templates = self.client.get_env_templates_list()
        self.assertEqual(200, resp.status)
        self.assertEqual(2, len(envs_templates))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_create_env_from_template(self):
        """Check the creation of an environment from a template."""
        resp, env_template = \
            self.create_env_template_with_apps('test_env_temp')
        self.assertEqual(200, resp.status)

        resp, env = self.create_env_from_template(env_template['id'],
                                                  "env")
        self.assertEqual(200, resp.status)
        self.assertIsNotNone(env)

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_delete_environment_with_wrong_env_id(self):
        """Check the deletion of an wrong environment template request."""
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_env_template,
                          None)

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_create_environment_with_wrong_payload(self):
        """Check the deletion of an wrong environment template request."""
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_env_template,
                          '  ')

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_double_delete_env_template(self):
        """Check the deletion of an wrong environment template request."""
        _, env_template = self.create_env_template('test_env_temp')

        self.client.delete_env_template(env_template['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.delete_env_template,
                          env_template['id'])

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_get_deleted_env_template(self):
        """Check the deletion of an wrong environment template request."""
        _, env_template = self.create_env_template('test_env_temp')

        self.client.delete_env_template(env_template['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.get_env_template,
                          env_template['id'])


class TestEnvTemplatesTenantIsolation(base.NegativeTestCase):

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_get_env_template_from_another_tenant(self):
        """It tests getting information from an environment
        template from another user.
        """
        _, env_template = self.create_env_template('test_env_temp')

        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_env_template, env_template['id'])

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_delete_env_template_from_another_tenant(self):
        """It tests deleting information from an environment
        template from another user.
        """
        _, env_template = self.create_env_template('test_env_temp')

        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_env_template,
                          env_template['id'])
