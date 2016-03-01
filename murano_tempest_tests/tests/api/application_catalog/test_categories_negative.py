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

from tempest.lib import exceptions
from tempest.test import attr

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils


class TestCategoriesNegative(base.BaseApplicationCatalogIsolatedAdminTest):

    @classmethod
    def resource_setup(cls):
        super(TestCategoriesNegative, cls).resource_setup()
        application_name = utils.generate_name(cls.__name__)
        name = utils.generate_name(cls.__name__)
        cls.category = cls.application_catalog_client.create_category(name)
        cls.abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        cls.package = cls.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [cls.category['name']],
             "tags": [], 'is_public': False})

    @classmethod
    def resource_cleanup(cls):
        os.remove(cls.abs_archive_path)
        cls.application_catalog_client.delete_package(cls.package['id'])
        cls.application_catalog_client.delete_category(cls.category['id'])
        super(TestCategoriesNegative, cls).resource_cleanup()

    @attr(type='negative')
    def test_delete_category_by_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.delete_category,
                          utils.generate_uuid())

    @attr(type='negative')
    def test_get_category_by_incorrect_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.application_catalog_client.get_category,
                          utils.generate_uuid())

    @attr(type='negative')
    def test_create_category_with_same_name(self):
        self.assertRaises(exceptions.Conflict,
                          self.application_catalog_client.create_category,
                          self.category['name'])

    @attr(type='negative')
    def test_delete_category_with_package(self):
        self.assertRaises(exceptions.Forbidden,
                          self.application_catalog_client.delete_category,
                          self.category['id'])
