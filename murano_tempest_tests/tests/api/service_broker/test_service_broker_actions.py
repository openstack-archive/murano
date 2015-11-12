# Copyright (c) 2015 Mirantis, Inc.
# All Rights Reserved.
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

import json
import os

from tempest import test

from murano_tempest_tests.tests.api.service_broker import base
from murano_tempest_tests import utils


class ServiceBrokerActionsTest(base.BaseServiceBrokerAdminTest):

    @test.attr(type=["gate"])
    def test_applications_listing(self):
        app_list = self.service_broker_client.get_applications_list()
        self.assertIsInstance(app_list, list)

    @test.attr(type=["smoke", "gate"])
    def test_provision_and_deprovision(self):
        application_name = utils.generate_name('cfapi')
        abs_archive_path, dir_with_archive, archive_name = \
            utils.prepare_package(application_name)
        self.addCleanup(os.remove, abs_archive_path)
        package = self.application_catalog_client.upload_package(
            application_name, archive_name, dir_with_archive,
            {"categories": [], "tags": [], 'is_public': True})
        self.addCleanup(self.application_catalog_client.delete_package,
                        package['id'])
        app_list = self.service_broker_client.get_applications_list()
        app = self.service_broker_client.get_application(application_name,
                                                         app_list)
        post_json = {}
        instance_id = utils.generate_uuid()
        service = self.service_broker_client.provision(
            instance_id, app['id'], app['plans'][0]['id'], post_json)
        self.wait_for_result(instance_id, 30)
        self.addCleanup(self.perform_deprovision, instance_id)
        self.assertIsInstance(json.loads(service), dict)
