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


class TestStaticActions(base.BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        if CONF.application_catalog.glare_backend:
            msg = ("Murano using GLARE backend. "
                   "Static actions tests will be skipped.")
            raise cls.skipException(msg)

        super(TestStaticActions, cls).resource_setup()

        application_name = utils.generate_name('test_repository_class')
        cls.abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name, add_class_name=True)
        cls.package = cls.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': False})

    @classmethod
    def resource_cleanup(cls):
        super(TestStaticActions, cls).resource_cleanup()
        os.remove(cls.abs_archive_path)
        cls.application_catalog_client.delete_package(cls.package['id'])

    @testtools.testcase.attr('smoke')
    def test_call_static_action_basic(self):
        action_result = self.application_catalog_client.call_static_action(
            class_name=self.package['class_definitions'][0],
            method_name='staticAction',
            args={'myName': 'John'})
        self.assertEqual('"Hello, John"', action_result)

    @testtools.testcase.attr('smoke')
    def test_call_static_action_full(self):
        action_result = self.application_catalog_client.call_static_action(
            class_name=self.package['class_definitions'][0],
            method_name='staticAction',
            package_name=self.package['fully_qualified_name'],
            class_version="<1", args={'myName': 'John'})
        self.assertEqual('"Hello, John"', action_result)
