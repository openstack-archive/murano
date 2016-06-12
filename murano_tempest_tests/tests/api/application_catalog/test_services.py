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

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils


class TestServices(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestServices, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.environment = cls.application_catalog_client.\
            create_environment(name)

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_environment(cls.environment['id'])
        super(TestServices, cls).resource_cleanup()

    @testtools.testcase.attr('smoke')
    def test_get_services_list(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        services_list = self.application_catalog_client.\
            get_services_list(self.environment['id'], session['id'])
        self.assertIsInstance(services_list, list)

    @testtools.testcase.attr('smoke')
    def test_create_and_delete_demo_service(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        services_list = self.application_catalog_client.\
            get_services_list(self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        services_list_ = self.application_catalog_client.\
            get_services_list(self.environment['id'], session['id'])
        self.assertEqual(len(services_list) + 1, len(services_list_))
        self.application_catalog_client.\
            delete_service(self.environment['id'],
                           session['id'],
                           service['?']['id'])
        services_list_ = self.application_catalog_client.\
            get_services_list(self.environment['id'], session['id'])
        self.assertEqual(len(services_list), len(services_list_))

    @testtools.testcase.attr('smoke')
    def test_get_service(self):
        session = self.application_catalog_client.\
            create_session(self.environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        self.environment['id'], session['id'])
        services_list = self.application_catalog_client.\
            get_services_list(self.environment['id'], session['id'])
        post_body = self._get_demo_app()
        service = self.application_catalog_client.\
            create_service(self.environment['id'], session['id'], post_body)
        services_list_ = self.application_catalog_client.\
            get_services_list(self.environment['id'], session['id'])
        self.assertEqual(len(services_list) + 1, len(services_list_))
        service_ = self.application_catalog_client.\
            get_service(self.environment['id'],
                        service['?']['id'],
                        session['id'])
        self.assertEqual(service, service_)

    @testtools.testcase.attr('smoke')
    def test_get_services_without_sess_id(self):
        services = self.application_catalog_client.\
            get_services_list(self.environment['id'], None)
        self.assertIsInstance(services, list)
        self.assertEqual([], services)
