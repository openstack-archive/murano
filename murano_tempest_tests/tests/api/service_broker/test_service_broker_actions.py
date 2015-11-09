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

from tempest import test

from murano_tempest_tests.tests.api.service_broker import base


class ServiceBrokerActionsTest(base.BaseServiceBrokerAdminTest):

    @test.attr(type=["smoke", "gate"])
    def test_applications_listing(self):
        app_list = self.service_broker_client.get_applications_list()
        self.assertIsInstance(app_list, list)
