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


class TestEnvironments(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        super(TestEnvironments, cls).resource_setup()
        name = utils.generate_name(cls.__name__)
        cls.environment = cls.application_catalog_client.\
            create_environment(name)

    @classmethod
    def resource_cleanup(cls):
        cls.application_catalog_client.\
            delete_environment(cls.environment['id'])
        super(TestEnvironments, cls).resource_cleanup()

    @testtools.testcase.attr('smoke')
    def test_list_environments(self):
        environments_list = self.application_catalog_client.\
            get_environments_list()
        self.assertIsInstance(environments_list, list)

    @testtools.testcase.attr('smoke')
    def test_create_and_delete_environment(self):
        environments_list = self.application_catalog_client.\
            get_environments_list()
        name = utils.generate_name('create_and_delete_env')
        environment = self.application_catalog_client.create_environment(name)
        self.assertEqual(name, environment['name'])
        upd_environments_list = self.application_catalog_client.\
            get_environments_list()
        self.assertEqual(len(environments_list) + 1,
                         len(upd_environments_list))
        self.application_catalog_client.delete_environment(environment['id'])
        upd_environments_list = self.application_catalog_client.\
            get_environments_list()
        self.assertEqual(len(environments_list),
                         len(upd_environments_list))

    @testtools.testcase.attr('smoke')
    def test_create_and_delete_environment_with_unicode_name(self):
        environments_list = self.application_catalog_client.\
            get_environments_list()
        name = u'$yaql \u2665 unicode'
        environment = self.application_catalog_client.create_environment(name)
        self.assertEqual(name, environment['name'])
        upd_environments_list = self.application_catalog_client.\
            get_environments_list()
        self.assertEqual(len(environments_list) + 1,
                         len(upd_environments_list))
        self.application_catalog_client.delete_environment(environment['id'])
        upd_environments_list = self.application_catalog_client.\
            get_environments_list()
        self.assertEqual(len(environments_list),
                         len(upd_environments_list))

    @testtools.testcase.attr('smoke')
    def test_get_environment(self):
        environment = self.application_catalog_client.\
            get_environment(self.environment['id'])
        self.assertEqual(self.environment['name'], environment['name'])

    @testtools.testcase.attr('smoke')
    def test_update_environment(self):
        environment = self.application_catalog_client.\
            update_environment(self.environment['id'])
        self.assertIsNot(self.environment['name'], environment['name'])
