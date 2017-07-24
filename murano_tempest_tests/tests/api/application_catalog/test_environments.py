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

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('32f26f2e-6c55-4e83-9d8c-023d86299d3e')
    def test_list_environments(self):
        environments_list = self.application_catalog_client.\
            get_environments_list()
        self.assertIsInstance(environments_list, list)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('a4c0b2fd-2c1b-473c-80cc-d433ceec4c80')
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

    @decorators.idempotent_id('52a06d5f-69e4-4184-a127-1bb13ce6dc7c')
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

    @decorators.idempotent_id('2b45d30b-3f1d-4482-805e-7cf15d19fe38')
    def test_get_environment(self):
        environment = self.application_catalog_client.\
            get_environment(self.environment['id'])
        self.assertEqual(self.environment['name'], environment['name'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('950f5bc1-3e5c-48d1-8b05-dc33303ce6f3')
    def test_update_environment(self):
        environment = self.application_catalog_client.\
            update_environment(self.environment['id'])
        self.assertIsNot(self.environment['name'], environment['name'])

    @decorators.idempotent_id('61001866-e885-4dda-9ac9-5b24c67a0e25')
    def test_get_environment_model(self):
        model = self.application_catalog_client.\
            get_environment_model(self.environment['id'])
        self.assertIsInstance(model, dict)
        self.assertIn('defaultNetworks', model)
        self.assertEqual(self.environment['name'], model['name'])
        self.assertEqual(model['?']['type'], "io.murano.Environment")

        net_name = self.application_catalog_client.\
            get_environment_model(self.environment['id'],
                                  path='/defaultNetworks/environment/name')
        self.assertEqual("{0}-network".format(self.environment['name']),
                         net_name)

    @decorators.idempotent_id('23416978-9701-49ff-9bb1-d312292a7f49')
    def test_update_environment_model(self):
        session = self.application_catalog_client. \
            create_session(self.environment['id'])
        patch = [{
            "op": "replace",
            "path": "/defaultNetworks/flat",
            "value": True
        }]
        new_model = self.application_catalog_client. \
            update_environment_model(self.environment['id'], patch,
                                     session['id'])
        self.assertTrue(new_model['defaultNetworks']['flat'])

        value_draft = self.application_catalog_client. \
            get_environment_model(self.environment['id'],
                                  '/defaultNetworks/flat',
                                  session['id'])
        self.assertTrue(value_draft)

        model_current = self.application_catalog_client. \
            get_environment_model(self.environment['id'])
        self.assertIsNone(model_current['defaultNetworks']['flat'])
