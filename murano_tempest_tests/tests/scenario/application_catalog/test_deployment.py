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

from murano_tempest_tests.tests.scenario.application_catalog import base
from murano_tempest_tests import utils

from tempest import config

CONF = config.CONF


class TestMuranoDeployment(base.BaseApplicationCatalogScenarioTest):

    @classmethod
    def resource_setup(cls):
        if not CONF.application_catalog.deployment_tests or \
                not CONF.application_catalog.linux_image:
            msg = "Application Catalog Scenario Deployment Tests will be " \
                  "skipped."
            raise cls.skipException(msg)
        super(TestMuranoDeployment, cls).resource_setup()

        cls.abs_archive_path = [None]*3
        cls.packages = [None]*3

        application_name = utils.generate_name('Apache')
        cls.abs_archive_path[0], dir_with_archive, archive_name = \
            utils.prepare_package(
                application_name,
                app='io.murano.apps.test.ApacheHttpServerCustom',
                manifest_required=False)

        if CONF.application_catalog.glare_backend:
            cls.client = cls.artifacts_client
        else:
            cls.client = cls.application_catalog_client

        cls.packages[0] = cls.client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": ["Web"], "tags": ["test"]})

        application_name = utils.generate_name('Lighttpd')
        cls.abs_archive_path[1], dir_with_archive, archive_name = \
            utils.prepare_package(
                application_name,
                app='io.murano.apps.test.Lighttpd',
                manifest_required=False)

        cls.packages[1] = cls.client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": ["Web"], "tags": ["test"]})

        application_name = utils.generate_name('UpdateExecutor')
        cls.abs_archive_path[2], dir_with_archive, archive_name = \
            utils.prepare_package(
                application_name,
                app='io.murano.apps.test.UpdateExecutor',
                manifest_required=False)

        cls.packages[2] = cls.client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": ["Web"], "tags": ["test"]})

    @classmethod
    def resource_cleanup(cls):

        cls.purge_stacks()
        [cls.client.delete_package(package['id']) for package in cls.packages]
        map(os.remove, cls.abs_archive_path)
        super(TestMuranoDeployment, cls).resource_cleanup()

    @testtools.testcase.attr('smoke')
    @testtools.testcase.attr('scenario')
    def test_app_deployment(self):

        """Test app deployment

        Scenario:
            1. Create environment
            2. Add ApacheHTTPServer application to the instance
            3. Deploy environment
            4. Make sure that deployment finished successfully
            5. Check that application is accessible
            6. Delete environment
        """

        post_body = self.apache()
        environment_name = utils.generate_name('Test_Murano')
        environment = self.application_catalog_client.create_environment(
            name=environment_name)
        self.addCleanup(self.environment_delete, environment['id'])
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.assertEqual(environment['id'], session['environment_id'])
        self.application_catalog_client.\
            create_service(environment['id'], session['id'], post_body)
        self.deploy_environment(environment, session)
        self.status_check(environment['id'],
                          [[post_body['instance']['name'], 22, 80]])

    @testtools.testcase.attr('smoke')
    @testtools.testcase.attr('scenario')
    def test_resources_deallocation(self):

        """Test resources deallocation

        Scenario:
            1. Create environment
            2. Add ApacheHTTPServer application to the instance
            3. Deploy environment
            4. Make sure that deployment finished successfully
            5. Check that application is accessible
            6. Remove application from environment
            7. Deploy environment
            8. Check that application is accessible
            9. Check that resources aren't used
            10. Delete environment
        """

        app_1_post_body = self.apache()
        app_2_post_body = self.apache()

        environment_name = utils.generate_name('Test_Murano')
        environment = self.application_catalog_client.create_environment(
            name=environment_name)
        self.addCleanup(self.environment_delete, environment['id'])
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.assertEqual(environment['id'], session['environment_id'])
        self.application_catalog_client.create_service(
            environment['id'], session['id'], app_1_post_body)
        self.application_catalog_client.create_service(
            environment['id'], session['id'], app_2_post_body)
        self.deploy_environment(environment, session)
        self.status_check(environment['id'],
                          [[app_1_post_body['instance']['name'], 22, 80]])

        environment = self.application_catalog_client.get_environment(
            environment['id'])
        app_for_remove = self.get_service(
            environment['id'], session['id'], app_1_post_body['name'])
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.application_catalog_client.delete_service(
            environment['id'], session['id'], app_for_remove['?']['id'])
        environment = self.application_catalog_client.get_environment(
            environment['id'])
        self.deploy_environment(environment, session)
        self.status_check(environment['id'],
                          [[app_2_post_body['instance']['name'], 22, 80]])

        instance_name = app_1_post_body['instance']['name']
        stack = self.get_stack_id(environment['id'])
        template = self.get_stack_template(stack)
        ip_addresses = '{0}-assigned-ip'.format(instance_name)
        floating_ip = '{0}-FloatingIPaddress'.format(instance_name)

        self.assertNotIn(ip_addresses, template['outputs'])
        self.assertNotIn(floating_ip, template['outputs'])
        self.assertNotIn(instance_name, template['resources'])

    @testtools.testcase.attr('smoke')
    @testtools.testcase.attr('scenario')
    def test_dependent_app(self):

        """Test dependent application

        Scenario:
            1. Create environment
            2. Add Update Executor application to the instance
            3. Add Dependent application
            4. Deploy environment
            5. Make sure that deployment finished successfully
            6. Check that application is accessible
            7. Delete environment
        """

        post_body = self.update_executor()
        environment_name = utils.generate_name('Test_Murano')
        environment = self.application_catalog_client.create_environment(
            name=environment_name)
        self.addCleanup(self.environment_delete, environment['id'])
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.assertEqual(environment['id'], session['environment_id'])
        updater = self.application_catalog_client.\
            create_service(environment['id'], session['id'], post_body)

        post_body = {
            "name": utils.generate_name("lighttest"),
            "updater": updater,
            "?": {
                "type": "io.murano.apps.test.Lighttpd",
                "id": utils.generate_uuid()
            }
        }

        self.application_catalog_client.create_service(
            environment['id'], session['id'], post_body)
        self.deploy_environment(environment, session)
        self.status_check(environment['id'],
                          [[updater['instance']['name'], 22, 80]])

    @testtools.testcase.attr('smoke')
    @testtools.testcase.attr('scenario')
    def test_simple_software_configuration(self):

        """Test simple software configuration

        Scenario:
            1. Create environment with name specified
            2. Add ApacheHTTPServer application to the instance with specific
            user name
            3. Deploy environment
            4. Make sure that deployment finished successfully
            5. Check that application is accessible
            6. Check that environment deployed with specific user name
            7. Delete environment
        """

        post_body = self.apache(userName=utils.generate_name('user'))
        username = post_body["userName"]
        environment_name = utils.generate_name('SSC-murano')
        environment = self.application_catalog_client.create_environment(
            name=environment_name)
        self.addCleanup(self.environment_delete, environment['id'])
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.assertEqual(environment['id'], session['environment_id'])
        self.application_catalog_client.\
            create_service(environment['id'], session['id'], post_body)
        self.deploy_environment(environment, session)
        self.status_check(environment['id'],
                          [[post_body['instance']['name'], 22, 80]])
        resp = self.check_path(
            environment['id'], '', post_body['instance']['name'])
        self.assertIn(username, resp.text, "Required information not found in "
                                           "response from server")
