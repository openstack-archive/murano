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
import testtools

from tempest import config

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils

CONF = config.CONF


class TestRepositorySanity(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        if CONF.application_catalog.glare_backend:
            msg = ("Murano using GLARE backend. "
                   "Repository tests will be skipped.")
            raise cls.skipException(msg)
        super(TestRepositorySanity, cls).resource_setup()

    @testtools.testcase.attr('smoke')
    def test_get_list_packages(self):
        package_list = self.application_catalog_client.get_list_packages()
        self.assertIsInstance(package_list, list)

    @testtools.testcase.attr('smoke')
    def test_upload_and_delete_package(self):
        application_name = utils.generate_name('package_test_upload')
        abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        self.addCleanup(os.remove, abs_archive_path)
        package = self.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': False})
        package_list = self.application_catalog_client.get_list_packages()
        self.assertIn(package, package_list)
        self.application_catalog_client.delete_package(package['id'])
        package_list = self.application_catalog_client.get_list_packages()
        self.assertNotIn(package, package_list)


class TestRepository(base.BaseApplicationCatalogIsolatedAdminTest):

    @classmethod
    def resource_setup(cls):
        if CONF.application_catalog.glare_backend:
            msg = ("Murano using GLARE backend. "
                   "Repository tests will be skipped.")
            raise cls.skipException(msg)

        super(TestRepository, cls).resource_setup()

        application_name = utils.generate_name('test_repository_class')
        cls.abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        cls.package = cls.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': False})

    @classmethod
    def resource_cleanup(cls):
        super(TestRepository, cls).resource_cleanup()
        os.remove(cls.abs_archive_path)
        cls.application_catalog_client.delete_package(cls.package['id'])

    @testtools.testcase.attr('smoke')
    def test_get_package(self):
        package = self.application_catalog_client.get_package(
            self.package['id'])
        self.assertEqual(self.package['tags'], package['tags'])

    @testtools.testcase.attr('smoke')
    def test_update_package(self):
        post_body = [
            {
                "op": "add",
                "path": "/tags",
                "value": ["im a test"]
            }
        ]

        result = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertIn("im a test", result['tags'])

        post_body = [
            {
                "op": "replace",
                "path": "/tags",
                "value": ["im bad:D"]
            }
        ]

        result = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertNotIn("im a test", result['tags'])
        self.assertIn("im bad:D", result['tags'])

        post_body = [
            {
                "op": "remove",
                "path": "/tags",
                "value": ["im bad:D"]
            }
        ]

        result = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertNotIn("im bad:D", result['tags'])

        post_body = [
            {
                "op": "replace",
                "path": "/is_public",
                "value": True
            }
        ]

        result = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertTrue(result['is_public'])

        post_body = [
            {
                "op": "replace",
                "path": "/enabled",
                "value": True
            }
        ]

        result = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertTrue(result['enabled'])

        post_body = [
            {
                "op": "replace",
                "path": "/description",
                "value": "New description"
            }
        ]

        result = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertEqual("New description", result['description'])

        post_body = [
            {
                "op": "replace",
                "path": "/name",
                "value": "New name"
            }
        ]

        result = self.application_catalog_client.update_package(
            self.package['id'], post_body)
        self.assertEqual("New name", result['name'])

    @testtools.testcase.attr('smoke')
    def test_download_package(self):
        self.application_catalog_client.download_package(self.package['id'])

    @testtools.testcase.attr('smoke')
    def test_get_ui_definitions(self):
        self.application_catalog_client.get_ui_definition(self.package['id'])

    @testtools.testcase.attr('smoke')
    def test_get_logo(self):
        self.application_catalog_client.get_logo(self.package['id'])
