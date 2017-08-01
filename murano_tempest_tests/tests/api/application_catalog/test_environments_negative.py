#    Copyright (c) 2016 Mirantis, Inc.
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


class TestEnvironmentsNegative(base.BaseApplicationCatalogTest):

    @decorators.attr(type='negative')
    @decorators.idempotent_id('9e245625-ce24-4068-916e-20a5608f6d5a')
    def test_delete_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_environment,
                          utils.generate_uuid())

    @decorators.attr(type='negative')
    @decorators.idempotent_id('1dae123c-27f4-4996-871e-31c66f76ee49')
    def test_double_delete_environment(self):
        name = utils.generate_name('double_del_negavive')
        environment = self.application_catalog_client.\
            create_environment(name)
        self.application_catalog_client.delete_environment(environment['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_environment,
                          environment['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('a8032052-5a48-48f0-b333-d1cefcfcbf5f')
    def test_get_deleted_environment(self):
        name = utils.generate_name('double_del_negavive')
        environment = self.application_catalog_client.\
            create_environment(name)
        self.application_catalog_client.delete_environment(environment['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_environment,
                          environment['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('f0b6102c-dd22-4f4d-9775-ce0a7a53d881')
    def test_update_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.update_environment,
                          None)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('03266970-2f9d-4b82-971f-532fe23d1027')
    def test_abandon_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.abandon_environment,
                          None)


class TestEnvironmentNegativeTenantIsolation(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestEnvironmentNegativeTenantIsolation, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.environment = cls.application_catalog_client.\
            create_environment(name)
        cls.alt_client = cls.get_client_with_isolated_creds(
            type_of_creds='alt')

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_environment(cls.environment['id'])
        super(TestEnvironmentNegativeTenantIsolation, cls).resource_cleanup()

    @decorators.attr(type='negative')
    @decorators.idempotent_id('0fc96a16-5df9-48b9-a681-ba5b3730e95b')
    def test_get_environment_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_environment,
                          self.environment['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('d3c6dc81-ed60-4346-869c-0a091c2fe5b8')
    def test_update_environment_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.update_environment,
                          self.environment['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('56aea1db-9314-4558-8b97-5fcd35fd6955')
    def test_delete_environment_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_environment,
                          self.environment['id'])
