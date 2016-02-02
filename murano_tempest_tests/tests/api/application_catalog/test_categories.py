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

import os

from tempest.test import attr

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils


class TestCategories(base.BaseApplicationCatalogIsolatedAdminTest):

    @classmethod
    def resource_setup(cls):
        super(TestCategories, cls).resource_setup()
        application_name = utils.generate_name(cls.__name__)
        cls.abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        cls.package = cls.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': False})
        name = utils.generate_name(cls.__name__)
        cls.category = cls.application_catalog_client.create_category(name)

    @classmethod
    def resource_cleanup(cls):
        os.remove(cls.abs_archive_path)
        cls.application_catalog_client.delete_package(cls.package['id'])
        cls.application_catalog_client.delete_category(cls.category['id'])
        super(TestCategories, cls).resource_cleanup()

    @attr(type='smoke')
    def test_get_list_categories(self):
        categories_list = self.application_catalog_client.list_categories()
        self.assertIsInstance(categories_list, list)

    @attr(type='smoke')
    def test_create_and_delete_category(self):
        name = utils.generate_name('create_and_delete_category')
        categories_list = self.application_catalog_client.list_categories()
        self.assertNotIn(name, categories_list)
        category = self.application_catalog_client.create_category(name)
        self.assertEqual(name, category['name'])
        categories_list = self.application_catalog_client.list_categories()
        self.assertIn(name, categories_list)
        self.application_catalog_client.delete_category(category['id'])
        categories_list = self.application_catalog_client.list_categories()
        self.assertNotIn(name, categories_list)

    @attr(type='smoke')
    def test_get_category(self):
        category = self.application_catalog_client.get_category(
            self.category['id'])
        self.assertEqual(self.category['id'], category['id'])
        self.assertEqual(self.category['name'], category['name'])

    @attr(type='smoke')
    def test_add_package_to_new_category_and_remove_it_from_category(self):
        category = self.application_catalog_client.get_category(
            self.category['id'])
        self.assertEqual(0, category['package_count'])

        post_body = [
            {
                "op": "add",
                "path": "/categories",
                "value": [category['name']]
            }
        ]

        package = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertIn(self.category['name'], package['categories'])
        category = self.application_catalog_client.get_category(
            self.category['id'])
        self.assertEqual(1, category['package_count'])
        self.assertEqual(1, len(category['packages']))

        post_body = [
            {
                "op": "remove",
                "path": "/categories",
                "value": [category['name']]
            }
        ]

        package = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertNotIn(self.category['name'], package['categories'])
        category = self.application_catalog_client.get_category(
            self.category['id'])
        self.assertEqual(0, category['package_count'])
        self.assertEqual(0, len(category['packages']))
