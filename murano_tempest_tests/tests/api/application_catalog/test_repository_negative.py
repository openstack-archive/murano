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
from tempest.lib import exceptions

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils

CONF = config.CONF


class TestRepositoryNegativeNotFound(base.BaseApplicationCatalogTest):
    @classmethod
    def resource_setup(cls):
        if CONF.application_catalog.glare_backend:
            msg = ("Murano using GLARE backend. "
                   "Repository tests will be skipped.")
            raise cls.skipException(msg)
        super(TestRepositoryNegativeNotFound, cls).resource_setup()

    @testtools.testcase.attr('negative')
    def test_update_package_with_incorrect_id(self):

        post_body = [
            {
                "op": "add",
                "path": "/tags",
                "value": ["im a test"]
            }
        ]

        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.update_package,
                          utils.generate_uuid(), post_body)

    @testtools.testcase.attr('negative')
    def test_get_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_package,
                          utils.generate_uuid())

    @testtools.testcase.attr('negative')
    def test_delete_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_package,
                          utils.generate_uuid())

    @testtools.testcase.attr('negative')
    def test_download_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.download_package,
                          utils.generate_uuid())

    @testtools.testcase.attr('negative')
    def test_get_ui_definition_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_ui_definition,
                          utils.generate_uuid())

    @testtools.testcase.attr('negative')
    def test_get_logo_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_logo,
                          utils.generate_uuid())


class TestRepositoryNegativeForbidden(base.BaseApplicationCatalogTest):

    # TODO(freerunner): I hope, that we can setup and cleanup resources
    # TODO(freerunner): dramatically better.
    @classmethod
    def resource_setup(cls):
        if CONF.application_catalog.glare_backend:
            msg = ("Murano using GLARE backend. "
                   "Repository tests will be skipped.")
            raise cls.skipException(msg)

        super(TestRepositoryNegativeForbidden, cls).resource_setup()

        application_name = utils.generate_name('package_test_upload')
        cls.abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        cls.package = cls.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': False})
        cls.alt_client = cls.get_client_with_isolated_creds(
            type_of_creds='alt')

    @classmethod
    def resource_cleanup(cls):
        super(TestRepositoryNegativeForbidden, cls).resource_cleanup()
        os.remove(cls.abs_archive_path)
        cls.application_catalog_client.delete_package(cls.package['id'])

    @testtools.testcase.attr('negative')
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

    @testtools.testcase.attr('negative')
    def test_get_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_package,
                          self.package['id'])

    @testtools.testcase.attr('negative')
    def test_delete_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_package,
                          self.package['id'])

    @testtools.testcase.attr('negative')
    def test_download_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.download_package,
                          self.package['id'])

    @testtools.testcase.attr('negative')
    def test_get_ui_definition_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_ui_definition,
                          self.package['id'])

    @testtools.testcase.attr('negative')
    def test_get_logo_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_logo,
                          self.package['id'])
