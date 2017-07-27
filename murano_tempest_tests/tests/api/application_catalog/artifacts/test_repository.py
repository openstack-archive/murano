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

from murano_tempest_tests.tests.api.application_catalog.artifacts import base
from murano_tempest_tests import utils

CONF = config.CONF


class TestRepositorySanity(base.BaseArtifactsTest):

    @classmethod
    def resource_setup(cls):
        if not CONF.application_catalog.glare_backend:
            msg = ("Murano is not using GLARE backend. "
                   "Skipping GLARE tests.")
            raise cls.skipException(msg)
        super(TestRepositorySanity, cls).resource_setup()

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('2818aaa0-6613-4bd9-8abe-02713121357a')
    def test_get_list_packages(self):
        package_list = self.artifacts_client.get_list_packages()
        self.assertIsInstance(package_list, list)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('bc717c98-5f6b-42a6-9131-43a711cfe848')
    def test_upload_and_delete_package(self):
        application_name = utils.generate_name('package_test_upload')
        abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        self.addCleanup(os.remove, abs_archive_path)
        package = self.artifacts_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': False})
        package_list = self.artifacts_client.get_list_packages()
        self.assertIn(package['id'], {pkg['id'] for pkg in package_list})
        self.artifacts_client.delete_package(package['id'])
        package_list = self.artifacts_client.get_list_packages()
        self.assertNotIn(package['id'], {pkg['id'] for pkg in package_list})
