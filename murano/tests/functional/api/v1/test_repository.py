#    Copyright (c) 2014 Mirantis, Inc.
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
import uuid

from tempest.lib import exceptions
from tempest.test import attr

from murano.tests.functional.api import base
from murano.tests.functional.common import utils as common_utils


class TestCaseRepository(base.TestCase, common_utils.ZipUtilsMixin):

    @classmethod
    def setUpClass(cls):

        super(TestCaseRepository, cls).setUpClass()

        cls.location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

        cls.zip_dir(cls.location, "DummyTestApp")

    def setUp(self):
        super(TestCaseRepository, self).setUp()

        self.packages = []

    def tearDown(self):
        super(TestCaseRepository, self).tearDown()

        for package in self.packages:
            try:
                self.client.delete_package(package['id'])
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):

        super(TestCaseRepository, cls).tearDownClass()

        os.remove(os.path.join(cls.location, "DummyTestApp.zip"))


class TestRepositorySanity(TestCaseRepository):

    @attr(type='smoke')
    def test_get_list_packages(self):
        resp, body = self.client.get_list_packages()

        self.assertEqual(200, resp.status)
        self.assertTrue(isinstance(body['packages'], list))

    @attr(type='smoke')
    def test_get_list_categories(self):
        resp, body = self.client.list_categories()

        self.assertEqual(200, resp.status)
        self.assertTrue(isinstance(body['categories'], list))

    @attr(type='smoke')
    def test_upload_and_delete_package(self):
        packages_list = self.client.get_list_packages()[1]
        for package in packages_list['packages']:
            if 'Dummy' in package['fully_qualified_name']:
                self.client.delete_package(package['id'])
        categorie = self.client.list_categories()[1]['categories'][0]
        packages_list = self.client.get_list_packages()[1]['packages']

        resp = self.client.upload_package(
            'testpackage',
            {"categories": [categorie], "tags": ["windows"]})
        self.packages.append(resp.json())

        _packages_list = self.client.get_list_packages()[1]['packages']

        self.assertEqual(200, resp.status_code)
        self.assertEqual(len(packages_list) + 1, len(_packages_list))

        resp = self.client.delete_package(resp.json()['id'])[0]

        _packages_list = self.client.get_list_packages()[1]['packages']

        self.assertEqual(200, resp.status)
        self.assertEqual(len(packages_list), len(_packages_list))


class TestRepositoryNegativeNotFound(base.NegativeTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRepositoryNegativeNotFound, cls).setUpClass()

        cls.id = uuid.uuid4().hex

    @attr(type='negative')
    def test_update_package_with_incorrect_id(self):

        post_body = [
            {
                "op": "add",
                "path": "/tags",
                "value": ["im a test"]
            }
        ]

        self.assertRaises(exceptions.NotFound,
                          self.client.update_package,
                          self.id,
                          post_body)

    @attr(type='negative')
    def test_get_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.get_package,
                          self.id)

    @attr(type='negative')
    def test_delete_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_package,
                          self.id)

    @attr(type='negative')
    def test_download_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.download_package,
                          self.id)

    @attr(type='negative')
    def test_get_ui_definition_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.get_ui_definition,
                          self.id)

    @attr(type='negative')
    def test_get_logo_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.get_logo,
                          self.id)


class TestRepositoryNegativeForbidden(base.NegativeTestCase,
                                      TestCaseRepository):
    @classmethod
    def setUpClass(cls):
        super(TestRepositoryNegativeForbidden, cls).setUpClass()

        cls.categorie = cls.client.list_categories()[1]['categories'][0]

        packages_list = cls.client.get_list_packages()[1]
        for package in packages_list['packages']:
            if 'Dummy' in package['fully_qualified_name']:
                cls.client.delete_package(package['id'])

        cls.package = cls.client.upload_package(
            'testpackage',
            {
                "categories": [cls.categorie],
                "tags": ["windows"],
                "is_public": False
            }
        ).json()

    @classmethod
    def tearDownClass(cls):

        super(TestRepositoryNegativeForbidden, cls).tearDownClass()

        cls.client.delete_package(cls.package['id'])
        cls.purge_creds()

    @attr(type='negative')
    def test_update_package_from_another_tenant(self):
        post_body = [
            {
                "op": "add",
                "path": "/tags",
                "value": ["im a test"]
            }
        ]

        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.update_package,
                          self.package['id'],
                          post_body)

    @attr(type='negative')
    def test_get_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_package,
                          self.package['id'])

    @attr(type='negative')
    def test_delete_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_package,
                          self.package['id'])

    @attr(type='negative')
    def test_download_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.download_package,
                          self.package['id'])

    @attr(type='negative')
    def test_get_ui_definition_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_ui_definition,
                          self.package['id'])

    @attr(type='negative')
    def test_get_logo_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_logo,
                          self.package['id'])


class TestRepository(TestCaseRepository):

    @classmethod
    def setUpClass(cls):

        super(TestRepository, cls).setUpClass()
        cls.categorie = cls.client.list_categories()[1]['categories'][0]

    def setUp(self):
        super(TestRepository, self).setUp()

        packages_list = self.client.get_list_packages()[1]
        for package in packages_list['packages']:
            if 'Dummy' in package['fully_qualified_name']:
                self.client.delete_package(package['id'])
        self.package = self.client.upload_package(
            'testpackage',
            {"categories": [self.categorie], "tags": ["windows"]}).json()
        self.packages.append(self.package)

    @attr(type='smoke')
    def test_get_package(self):
        resp, body = self.client.get_package(self.package['id'])

        self.assertEqual(200, resp.status)
        self.assertEqual(self.package['tags'], body['tags'])

    @attr(type='smoke')
    def test_update_package(self):
        post_body = [
            {
                "op": "add",
                "path": "/tags",
                "value": ["im a test"]
            }
        ]

        resp, body = self.client.update_package(self.package['id'], post_body)

        self.assertEqual(200, resp.status)
        self.assertIn("im a test", body['tags'])

        post_body = [
            {
                "op": "replace",
                "path": "/tags",
                "value": ["im bad:D"]
            }
        ]

        resp, body = self.client.update_package(self.package['id'], post_body)

        self.assertEqual(200, resp.status)
        self.assertNotIn("im a test", body['tags'])
        self.assertIn("im bad:D", body['tags'])

        post_body = [
            {
                "op": "remove",
                "path": "/tags",
                "value": ["im bad:D"]
            }
        ]

        resp, body = self.client.update_package(self.package['id'], post_body)

        self.assertEqual(200, resp.status)
        self.assertNotIn("im bad:D", body['tags'])

        post_body = [
            {
                "op": "replace",
                "path": "/is_public",
                "value": True
            }
        ]

        resp, body = self.client.update_package(self.package['id'], post_body)

        self.assertEqual(200, resp.status)
        self.assertTrue(body['is_public'])

        post_body = [
            {
                "op": "replace",
                "path": "/enabled",
                "value": True
            }
        ]

        resp, body = self.client.update_package(self.package['id'], post_body)

        self.assertEqual(200, resp.status)
        self.assertTrue(body['enabled'])

        post_body = [
            {
                "op": "replace",
                "path": "/description",
                "value": "New description"
            }
        ]

        resp, body = self.client.update_package(self.package['id'], post_body)

        self.assertEqual(200, resp.status)
        self.assertEqual("New description", body['description'])

        post_body = [
            {
                "op": "replace",
                "path": "/name",
                "value": "New name"
            }
        ]

        resp, body = self.client.update_package(self.package['id'], post_body)

        self.assertEqual(200, resp.status)
        self.assertEqual("New name", body['name'])

    @attr(type='smoke')
    def test_download_package(self):
        resp = self.client.download_package(self.package['id'])[0]

        self.assertEqual(200, resp.status)

    @attr(type='smoke')
    def test_get_ui_definitions(self):
        resp = self.client.get_ui_definition(self.package['id'])[0]

        self.assertEqual(200, resp.status)

    @attr(type='smoke')
    def test_get_logo(self):
        resp, body = self.client.get_logo(self.package['id'])

        self.assertEqual(200, resp.status)
        self.assertTrue(isinstance(body, str))
