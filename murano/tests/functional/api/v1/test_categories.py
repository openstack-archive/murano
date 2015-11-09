#    Copyright (c) 2015 Mirantis, Inc.
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

from nose.plugins.attrib import attr as tag
from tempest.test import attr
from tempest_lib import exceptions

from murano.tests.functional.api import base


class TestCategories(base.TestObjectCreation):

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_get_list_categories(self):
        resp, body = self.client.list_categories()

        self.assertEqual(200, resp.status)
        self.assertTrue(isinstance(body['categories'], list))

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_create_and_delete_category(self):
        name = base.generate_name('test')

        categories_list = self.client.list_categories()[1]['categories']
        self.assertNotIn(name, categories_list)

        resp, body = self.client.create_category(name)
        self.assertEqual(200, resp.status)
        self.assertEqual(name, body['name'])

        categories_list = self.client.list_categories()[1]['categories']
        self.assertIn(name, categories_list)

        resp = self.client.delete_category(body['id'])[0]
        self.assertEqual(200, resp.status)

        categories_list = self.client.list_categories()[1]['categories']
        self.assertNotIn(name, categories_list)

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_get_category(self):
        name = base.generate_name('test')

        body = self.create_category(name)[1]
        resp, category = self.client.get_category(body['id'])

        self.assertEqual(body['id'], category['id'])
        self.assertEqual(name, category['name'])
        self.assertEqual(0, category['package_count'])

    @tag('all', 'coverage')
    @attr(type='smoke')
    def test_add_package_to_new_category(self):
        name = base.generate_name('test')
        path_to_zip = self.create_app_zip_archive("DummyTestApp")

        body = self.create_category(name)[1]
        category = self.client.get_category(body['id'])[1]

        self.assertEqual(0, category['package_count'])

        self.upload_package(
            'testpackage',
            {"categories": [name], "tags": []},
            path_to_zip
        )
        category = self.client.get_category(body['id'])[1]

        self.assertEqual(1, category['package_count'])
        self.assertEqual(1, len(category['packages']))


class TestCategoriesNegative(base.TestObjectCreation):

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_delete_category_by_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_category,
                          '123456')

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_get_category_by_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.get_category,
                          '123456')

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_create_category_with_same_name(self):
        name = base.generate_name('test')

        self.create_category(name)[1]
        self.assertRaises(exceptions.Conflict,
                          self.create_category,
                          name)

    @tag('all', 'coverage')
    @attr(type='negative')
    def test_delete_category_with_package(self):
        name = base.generate_name('test')
        path_to_zip = self.create_app_zip_archive("DummyTestApp")

        body = self.create_category(name)[1]
        self.upload_package(
            'testpackage',
            {"categories": [name], "tags": []},
            path_to_zip
        )
        self.assertRaises(exceptions.Forbidden,
                          self.client.delete_category,
                          body['id'])
