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

import testtools

from tempest.lib import exceptions

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils


class TestEnvironmentsNegative(base.BaseApplicationCatalogTest):

    @testtools.testcase.attr('negative')
    def test_delete_environment_with_wrong_env_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_environment,
                          utils.generate_uuid())

    @testtools.testcase.attr('negative')
    def test_double_delete_environment(self):
        name = utils.generate_name('double_del_negavive')
        environment = self.application_catalog_client.\
            create_environment(name)
        self.application_catalog_client.delete_environment(environment['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_environment,
                          environment['id'])

    @testtools.testcase.attr('negative')
    def test_get_deleted_environment(self):
        name = utils.generate_name('double_del_negavive')
        environment = self.application_catalog_client.\
            create_environment(name)
        self.application_catalog_client.delete_environment(environment['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_environment,
                          environment['id'])


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

    @testtools.testcase.attr('negative')
    def test_get_environment_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_environment,
                          self.environment['id'])

    @testtools.testcase.attr('negative')
    def test_update_environment_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.update_environment,
                          self.environment['id'])

    @testtools.testcase.attr('negative')
    def test_delete_environment_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_environment,
                          self.environment['id'])
