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


class TestServicesNegative(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestServicesNegative, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.environment = cls.application_catalog_client.\
            create_environment(name)

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_environment(cls.environment['id'])
        super(TestServicesNegative, cls).resource_cleanup()

    @testtools.testcase.attr('negative')
    def test_get_services_list_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_services_list,
                          None,
                          session['id'])

    @testtools.testcase.attr('negative')
    def test_get_services_list_after_delete_env(self):
        name = utils.generate_name("get_services_list_after_delete_env")
        environment = self.application_catalog_client.create_environment(name)
        session = self.application_catalog_client.\
            create_session(environment['id'])
        self.application_catalog_client.delete_environment(environment['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_services_list,
                          environment['id'],
                          session['id'])

    @testtools.testcase.attr('negative')
    def test_get_services_list_after_delete_session(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.application_catalog_client.\
            delete_session(self.environment['id'], session['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_services_list,
                          self.environment['id'],
                          session['id'])

    @testtools.testcase.attr('negative')
    def test_create_service_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.create_service,
                          None,
                          session['id'],
                          post_body)

    @testtools.testcase.attr('negative')
    def test_create_service_without_sess_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        self.assertRaises(exceptions.BadRequest,
                          self.application_catalog_client.create_service,
                          self.environment['id'],
                          "",
                          post_body)

    @testtools.testcase.attr('negative')
    def test_delete_service_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_service,
                          "",
                          session['id'],
                          service['?']['id'])

    @testtools.testcase.attr('negative')
    def test_delete_service_without_session_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        self.assertRaises(exceptions.BadRequest,
                          self.application_catalog_client.delete_service,
                          self.environment['id'],
                          "",
                          service['?']['id'])

    @testtools.testcase.attr('negative')
    def test_double_delete_service(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        self.application_catalog_client.\
            delete_service(self.environment['id'],
                           session['id'],
                           service['?']['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_service,
                          self.environment['id'],
                          session['id'],
                          service['?']['id'])

    @testtools.testcase.attr('negative')
    def test_get_service_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_service,
                          None,
                          session['id'],
                          service['?']['id'])


class TestServicesNegativeTenantIsolation(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestServicesNegativeTenantIsolation, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.environment = cls.application_catalog_client.\
            create_environment(name)
        cls.alt_client = cls.get_client_with_isolated_creds(
            type_of_creds='alt')

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_environment(cls.environment['id'])
        super(TestServicesNegativeTenantIsolation, cls).resource_cleanup()

    @testtools.testcase.attr('negative')
    def test_get_list_services_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_services_list,
                          self.environment['id'],
                          session['id'])

    @testtools.testcase.attr('negative')
    def test_create_service_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.create_service,
                          self.environment['id'],
                          session['id'],
                          post_body)

    @testtools.testcase.attr('negative')
    def test_delete_service_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_service,
                          self.environment['id'],
                          session['id'],
                          service['?']['id'])

    @testtools.testcase.attr('negative')
    def test_get_service_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_service,
                          self.environment['id'],
                          session['id'],
                          service['?']['id'])
