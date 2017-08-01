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

from tempest import config
from tempest.lib import decorators
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('49c557f4-789c-4d9c-8f48-0ba6bea4f234')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('72590141-5046-424a-bed2-17e7b7aabd9a')
    def test_get_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_package,
                          utils.generate_uuid())

    @decorators.attr(type='negative')
    @decorators.idempotent_id('09e3f9d9-40ae-4d5c-a488-4137e3abd7a2')
    def test_delete_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_package,
                          utils.generate_uuid())

    @decorators.attr(type='negative')
    @decorators.idempotent_id('a3cbcb58-7e46-47e9-a633-e3fc296681a9')
    def test_download_package_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.download_package,
                          utils.generate_uuid())

    @decorators.attr(type='negative')
    @decorators.idempotent_id('46799c58-8fe1-4d30-91a9-6067af780b32')
    def test_get_ui_definition_with_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_ui_definition,
                          utils.generate_uuid())

    @decorators.attr(type='negative')
    @decorators.idempotent_id('062ad8ab-6b5e-43ed-8331-b4bcd849b06e')
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
        os.remove(cls.abs_archive_path)
        cls.application_catalog_client.delete_package(cls.package['id'])
        super(TestRepositoryNegativeForbidden, cls).resource_cleanup()

    @decorators.attr(type='negative')
    @decorators.idempotent_id('29f9b3f1-8e8a-4305-a593-e3055e098666')
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

    @decorators.attr(type='negative')
    @decorators.idempotent_id('75b57ded-6077-436f-97f8-d3087f2f3b77')
    def test_get_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_package,
                          self.package['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('1d9f8f74-8aca-4ee8-be0d-ac5b9d5a7dcd')
    def test_delete_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.delete_package,
                          self.package['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('a1467fed-cd6f-44dd-b79c-ea0f91e082dc')
    def test_download_package_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.download_package,
                          self.package['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('b6074261-f981-4c15-9cd6-5811bd75127a')
    def test_get_ui_definition_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_ui_definition,
                          self.package['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('a5a3c2bb-3fde-49cb-ae4c-c454d7eb956b')
    def test_get_logo_from_another_tenant(self):
        self.assertRaises(exceptions.Forbidden,
                          self.alt_client.get_logo,
                          self.package['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('12928ec7-bd31-415d-9260-5c488aebd4c7')
    def test_publicize_package_as_non_admin_user(self):
        # Given a package that isn't public
        application_name = utils.generate_name('test_publicize_package_'
                                               'as_non_admin_user')
        abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        self.addCleanup(os.remove, abs_archive_path)
        package = self.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': False})
        self.addCleanup(self.application_catalog_client.delete_package,
                        package['id'])

        # When package is publicized, then the method throws an exception
        post_body = [
            {
                "op": "replace",
                "path": "/is_public",
                "value": True
            }
        ]
        self.assertRaises(exceptions.Forbidden,
                          self.application_catalog_client.update_package,
                          package['id'],
                          post_body)
