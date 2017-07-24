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
from tempest.lib import decorators

from murano_tempest_tests.tests.scenario.application_catalog import base
from murano_tempest_tests import utils

CONF = config.CONF


class TestSecurityGroups(base.BaseApplicationCatalogScenarioTest):

    @classmethod
    def resource_setup(cls):
        super(TestSecurityGroups, cls).resource_setup()
        cls.linux = CONF.application_catalog.linux_image
        application_name = utils.generate_name('VM')
        cls.abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(
                application_name,
                app='io.murano.apps.test.VM',
                manifest_required=False)
        if CONF.application_catalog.glare_backend:
            cls.client = cls.artifacts_client
        else:
            cls.client = cls.application_catalog_client
        cls.package = cls.client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": ["Web"], "tags": ["test"]})

    @classmethod
    def resource_cleanup(cls):
        cls.client.delete_package(cls.package['id'])
        os.remove(cls.abs_archive_path)
        super(TestSecurityGroups, cls).resource_cleanup()

    @decorators.idempotent_id('1344f041-3f7a-4e75-acfc-36b050ccec82')
    @testtools.testcase.attr('smoke')
    @testtools.testcase.attr('scenario')
    def test_deploy_app_with_murano_defined_security_group(self):
        name = utils.generate_name('testMurano')
        environment = self.application_catalog_client.create_environment(name)
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.application_catalog_client.create_service(
            environment['id'], session['id'], self.vm_test())
        self.deploy_environment(environment, session)
        instance_id = self.get_instance_id('testMurano')
        security_groups = self.servers_client.list_security_groups_by_server(
            instance_id).get('security_groups')
        self.assertEqual(len(security_groups), 1)
        self.assertEqual(len(security_groups[0].get('rules')), 4)

    @decorators.idempotent_id('c52cb4a2-53dd-44c3-95d5-7e1606954caa')
    @testtools.testcase.attr('smoke')
    @testtools.testcase.attr('scenario')
    def test_deploy_app_with_user_defined_security_group(self):
        name = utils.generate_name('testMurano')
        environment = self.application_catalog_client.create_environment(name)
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.application_catalog_client.create_service(
            environment['id'], session['id'],
            self.vm_test(securityGroups=['default']))
        self.deploy_environment(environment, session)
        instance_id = self.get_instance_id('testMurano')
        security_groups = self.servers_client.list_security_groups_by_server(
            instance_id).get('security_groups')
        self.assertEqual(len(security_groups), 1)
        self.assertEqual('default', security_groups[0].get('name'))
