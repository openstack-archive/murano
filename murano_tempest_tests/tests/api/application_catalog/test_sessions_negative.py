# Copyright (c) 2016 Mirantis, Inc.
# All Rights Reserved.
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


class TestSessionsNegative(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestSessionsNegative, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.environment = cls.application_catalog_client.\
            create_environment(name)

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_environment(cls.environment['id'])
        super(TestSessionsNegative, cls).resource_cleanup()

    @attr(type='negative')
    def test_create_session_before_env(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.create_session,
                          utils.generate_uuid())

    @attr(type='negative')
    def test_delete_session_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.BadRequest,
                          self.application_catalog_client.delete_session,
                          None, session['id'])

    @attr(type='negative')
    def test_get_session_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.BadRequest,
                          self.application_catalog_client.get_session,
                          None, session['id'])

    @attr(type='negative')
    def test_get_session_after_delete_env(self):
        name = utils.generate_name('get_session_after_delete_env')
        environment = self.application_catalog_client.create_environment(name)
        session = self.application_catalog_client.\
            create_session(environment['id'])
        self.application_catalog_client.delete_environment(environment['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_session,
                          environment['id'], session['id'])

    @attr(type='negative')
    def test_double_delete_session(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.application_catalog_client.delete_session(self.environment['id'],
                                                       session['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_session,
                          self.environment['id'], session['id'])


class TestSessionsNegativeTenantIsolation(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestSessionsNegativeTenantIsolation, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.environment = cls.application_catalog_client.\
            create_environment(name)
        cls.alt_client = cls.get_client_with_isolated_creds(
            type_of_creds='alt')

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_environment(cls.environment['id'])
        super(TestSessionsNegativeTenantIsolation, cls).resource_cleanup()

    @attr(type='negative')
    def test_create_session_in_env_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.create_session,
                          self.environment['id'])

    @attr(type='negative')
    def test_delete_session_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_session,
                          self.environment['id'], session['id'])

    @attr(type='negative')
    def test_get_session_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_session,
                          self.environment['id'], session['id'])

    @attr(type='negative')
    def test_deploy_session_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.deploy_session,
                          self.environment['id'], session['id'])
