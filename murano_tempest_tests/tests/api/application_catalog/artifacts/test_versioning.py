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
import six
import testtools

from tempest import config

from murano_tempest_tests.tests.api.application_catalog.artifacts import base
from murano_tempest_tests import utils

CONF = config.CONF


class TestVersioning(base.BaseArtifactsTest):

    @classmethod
    def resource_setup(cls):
        if not CONF.application_catalog.glare_backend:
            msg = ("Murano is not using GLARE backend. "
                   "Skipping GLARE tests.")
            raise cls.skipException(msg)
        super(TestVersioning, cls).resource_setup()

        application_name = utils.generate_name('package_test')
        # create first package
        version1 = '1.0.0'
        package1, _ = cls.upload_package(application_name,
                                         version=version1)

        # create second package
        version2 = '2.0.0'
        package2, path1 = cls.upload_package(application_name,
                                             version=version2)

        # create package with require >=2.0.0 for 2.0.0 package
        expected_version = '>=2.0.0'
        main_app_name = utils.generate_name('main_package_test')
        require = [(package2['name'], expected_version)]
        package3, path2 = cls.upload_package(main_app_name, require=require)

        cls.packages = {
            '1.0.0': package1,
            '2.0.0': package2,
            'require_for_2.0.0': package3,
        }
        cls.abs_archive_paths = [path1, path2]

    @classmethod
    def resource_cleanup(cls):
        for pkg in six.itervalues(cls.packages):
            cls.artifacts_client.delete_package(pkg['id'])
        map(os.remove, cls.abs_archive_paths)
        super(TestVersioning, cls).resource_cleanup()

    @testtools.testcase.attr('smoke')
    def test_availability_of_packages_with_different_versions(self):
        """Test availability of packages with different versions.

        1) Check two packages to have the same names.
        2) Check two packages to have different ids.
        3) Check two packages to be in repository.
        """
        self.assertEqual(self.packages['1.0.0']['name'],
                         self.packages['2.0.0']['name'])
        self.assertNotEqual(self.packages['1.0.0']['id'],
                            self.packages['2.0.0']['id'])

        # check packages availability
        artifact_packages = {pkg['id'] for pkg in
                             self.artifacts_client.get_list_packages()}

        self.assertIn(self.packages['1.0.0']['id'], artifact_packages)
        self.assertIn(self.packages['2.0.0']['id'], artifact_packages)

    @testtools.testcase.attr('smoke')
    def test_deploy_packages_with_different_versions(self):
        """Test deployment of packages with different versions.

        1) Create environment.
        2) Add package with version 1.0.0 to the environment.
        3) Add package with version 2.0.0 to the environment.
        4) Deploy environment.
        5) Check if deployment status ok.
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

        # add first application
        object_model = self.create_obj_model(self.packages['1.0.0'])

        self.application_catalog_client.create_service(
            environment['id'], session['id'], object_model)

        # add second application
        object_model = self.create_obj_model(self.packages['2.0.0'])

        self.application_catalog_client.create_service(
            environment['id'], session['id'], object_model)

        self.application_catalog_client.deploy_session(
            environment['id'], session['id'])

        deploy_result = utils.wait_for_environment_deploy(
            self.application_catalog_client, environment['id'])['status']

        self.assertEqual(deploy_result, 'ready')

    @testtools.testcase.attr('smoke')
    def test_deploy_package_with_required_package_version(self):
        """Test deployment of package which requires package with present version.

        1) Create environment.
        2) Add to the environment package which requires version 2.0.0 of the
        package, which is present with versions 1.0.0 and 2.0.0 in repository.
        3) Deploy environment.
        4) Check if deployment status ok.
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
            self.packages['require_for_2.0.0'])

        self.application_catalog_client.create_service(
            environment['id'], session['id'], object_model)

        self.application_catalog_client.deploy_session(
            environment['id'], session['id'])

        deploy_result = utils.wait_for_environment_deploy(
            self.application_catalog_client, environment['id'])['status']

        self.assertEqual(deploy_result, 'ready')
