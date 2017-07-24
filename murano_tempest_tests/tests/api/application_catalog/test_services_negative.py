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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('5f1dd3f4-170f-4020-bbf6-3d7c277957a8')
    def test_get_services_list_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_services_list,
                          None,
                          session['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('e17972e2-4c5c-4b25-a6cd-82eb2d64897a')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('e4ffe0b1-deb0-4f33-9790-6e6dc8bcdecb')
    def test_get_services_list_after_delete_session(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.application_catalog_client.\
            delete_session(self.environment['id'], session['id'])
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_services_list,
                          self.environment['id'],
                          session['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('d88880e2-63de-47a0-b29b-a3810b5715e6')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('1d9311af-917a-4a29-b42f-62377369d346')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('b22f2232-a6d3-4770-b26e-a1e0ccf62d60')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('04b4a8b7-3cf6-494a-8741-151305909893')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('2d040e59-3af3-47a2-8d87-eef70920cd65')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('a742e411-e572-4aed-ba91-dba8db694039')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('ded0b813-c36e-4108-8be2-c4b1e061f4e9')
    def test_put_services_without_env_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        put_body = [self._get_demo_app()]
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.update_services,
                          None,
                          session['id'],
                          put_body)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('4ab7a7ac-1939-404a-8cb7-feaadc06ae3f')
    def test_put_services_without_sess_id(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        put_body = [self._get_demo_app()]
        self.assertRaises(exceptions.BadRequest,
                          self.application_catalog_client.update_services,
                          self.environment['id'],
                          "",
                          put_body)


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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('014050a1-4f8d-4a9b-8332-3eb03d10ba64')
    def test_get_list_services_in_env_from_another_tenant(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_services_list,
                          self.environment['id'],
                          session['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('b2c70134-0537-4912-a6c7-23d477f62764')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('264f5854-5fce-4186-987a-98d4fbb67093')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('ff557e1f-a775-4a10-9265-2fa653179c4c')
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
