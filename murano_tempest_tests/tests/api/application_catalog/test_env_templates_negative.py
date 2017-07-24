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

from tempest.lib import decorators
from tempest.lib import exceptions

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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('022d0889-c5b3-4853-934f-533b43dfa89f')
    def test_clone_env_template_private(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.clone_env_template,
                          self.env_template['id'], 'cloned_template')

    @decorators.attr(type='negative')
    @decorators.idempotent_id('1132afa7-6965-4f48-a4ed-aeedba25ad8c')
    def test_delete_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_env_template,
                          None)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('a344b0be-d07d-4dfe-916d-900d93e44425')
    def test_create_environment_with_wrong_payload(self):
        self.assertRaises(exceptions.BadRequest,
                          self.application_catalog_client.create_env_template,
                          '  ')

    @decorators.attr(type='negative')
    @decorators.idempotent_id('fa2efa91-75c0-430f-942d-f52fe208cb16')
    def test_double_delete_env_template(self):
        name = utils.generate_name('double_delete_env_template')
        env_template = self.application_catalog_client.\
            create_env_template(name)
        self.application_catalog_client.delete_env_template(
            env_template['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_env_template,
                          env_template['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('3641cfa9-e74e-4e74-af09-6d0c7d4634fc')
    def test_get_deleted_env_template(self):
        name = utils.generate_name('get_deleted_env_template')
        env_template = self.application_catalog_client.\
            create_env_template(name)
        self.application_catalog_client.delete_env_template(
            env_template['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_env_template,
                          env_template['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('106fe373-8232-4fb4-870f-290ffa3b475b')
    def test_create_environment_template_with_same_name(self):
        self.assertRaises(exceptions.Conflict,
                          self.application_catalog_client.create_env_template,
                          self.name)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('07f56f09-3ca4-4d2a-8713-6306f2c3c4f8')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('bdf6febf-51aa-4b0a-b0e8-645e4df2531c')
    def test_get_env_template_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_env_template,
                          self.env_template['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('b664b388-489f-4036-918a-18fa34a2a04e')
    def test_delete_env_template_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_env_template,
                          self.env_template['id'])
