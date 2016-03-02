# Copyright (c) 2015 Telefonica I+D.
# Copyright (c) 2016 Mirantis, Inc.
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

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils


class TestEnvironmentTemplatesNegative(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestEnvironmentTemplatesNegative, cls).resource_setup()
        cls.name = utils.generate_name(cls.__name__)
        cls.env_template = cls.application_catalog_client.\
            create_env_template(cls.name)
        cls.environment = cls.application_catalog_client.\
            create_environment(cls.name)
        cls.alt_client = cls.get_client_with_isolated_creds('alt')

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_env_template(cls.env_template['id'])
        cls.application_catalog_client.delete_environment(
            cls.environment['id'])
        super(TestEnvironmentTemplatesNegative, cls).resource_cleanup()

    @attr(type='negative')
    def test_clone_env_template_private(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.clone_env_template,
                          self.env_template['id'], 'cloned_template')

    @attr(type='negative')
    def test_delete_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_env_template,
                          None)

    @attr(type='negative')
    def test_create_environment_with_wrong_payload(self):
        self.assertRaises(exceptions.BadRequest,
                          self.application_catalog_client.create_env_template,
                          '  ')

    @attr(type='negative')
    def test_double_delete_env_template(self):
        name = utils.generate_name('double_delete_env_template')
        env_template = self.application_catalog_client.\
            create_env_template(name)
        self.application_catalog_client.delete_env_template(
            env_template['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_env_template,
                          env_template['id'])

    @attr(type='negative')
    def test_get_deleted_env_template(self):
        name = utils.generate_name('get_deleted_env_template')
        env_template = self.application_catalog_client.\
            create_env_template(name)
        self.application_catalog_client.delete_env_template(
            env_template['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_env_template,
                          env_template['id'])

    @attr(type='negative')
    def test_create_environment_template_with_same_name(self):
        self.assertRaises(exceptions.Conflict,
                          self.application_catalog_client.create_env_template,
                          self.name)

    @attr(type='negative')
    def test_create_env_from_template_witch_existing_name(self):
        self.assertRaises(exceptions.Conflict,
                          self.application_catalog_client.
                          create_env_from_template,
                          self.env_template['id'],
                          self.name)


class TestEnvTemplatesTenantIsolation(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestEnvTemplatesTenantIsolation, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.env_template = cls.application_catalog_client.\
            create_env_template(name)
        cls.alt_client = cls.get_client_with_isolated_creds('alt')

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_env_template(cls.env_template['id'])
        super(TestEnvTemplatesTenantIsolation, cls).resource_cleanup()

    @attr(type='negative')
    def test_get_env_template_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_env_template,
                          self.env_template['id'])

    @attr(type='negative')
    def test_delete_env_template_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_env_template,
                          self.env_template['id'])
