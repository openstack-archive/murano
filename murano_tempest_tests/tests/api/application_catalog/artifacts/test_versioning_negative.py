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


class TestVersioningNegative(base.BaseArtifactsTest):

    @classmethod
    def resource_setup(cls):
        if not CONF.application_catalog.glare_backend:
            msg = ("Murano is not using GLARE backend. "
                   "Skipping GLARE tests.")
            raise cls.skipException(msg)
        super(TestVersioningNegative, cls).resource_setup()

        # create package with version 1.0.0
        application_name = utils.generate_name('package_test')
        provided_version = '1.0.0'
        package1, path1 = cls.upload_package(
            application_name, version=provided_version)

        # main application
        expected_version = '2.0.0'
        main_app_name = utils.generate_name('main_package_test')
        require = [(package1['name'], expected_version)]
        package2, path2 = cls.upload_package(main_app_name, require=require)

        cls.packages = {
            '1.0.0': package1,
            'require_for_1.0.0': package2
        }
        cls.abs_archive_paths = [path1, path2]

    @classmethod
    def resource_cleanup(cls):
        for pkg in cls.packages.values():
            cls.artifacts_client.delete_package(pkg['id'])
        map(os.remove, cls.abs_archive_paths)
        super(TestVersioningNegative, cls).resource_cleanup()

    @decorators.attr(type=['negative', 'smoke'])
    @decorators.idempotent_id('c72fcd24-4694-4479-b550-bdd8cf0bd348')
    def test_deploy_package_with_no_required_package_version(self):
        """Test deployment of package which requires package with absent version.

        1) Create environment.
        2) Add to the environment package which requires version 2.0.0 of the
        package, which is present with version 1.0.0 only in repository.
        3) Deploy environment.
        4) Check if deployment status failure.
        """

        # create environment
        environment_name = utils.generate_name('create_environment')
        environment = self.application_catalog_client.create_environment(
            environment_name)
        self.addCleanup(self.application_catalog_client.delete_environment,
                        environment['id'])

        # create session
        session = self.application_catalog_client.create_session(
            environment['id'])

        object_model = self.create_obj_model(
            self.packages['require_for_1.0.0'])

        self.application_catalog_client.create_service(
            environment['id'], session['id'], object_model)

        self.application_catalog_client.deploy_session(
            environment['id'], session['id'])

        deploy_result = utils.wait_for_environment_deploy(
            self.application_catalog_client, environment['id'])['status']

        self.assertEqual(deploy_result, 'deploy failure')
