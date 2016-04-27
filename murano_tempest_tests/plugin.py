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

import os

from tempest import config
from tempest.test_discover import plugins

from murano_tempest_tests import config as config_application_catalog


class MuranoTempestPlugin(plugins.TempestPlugin):
    def load_tests(self):
        base_path = os.path.split(os.path.dirname(
            os.path.abspath(__file__)))[0]
        test_dir = "murano_tempest_tests/tests"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        config.register_opt_group(
            conf, config_application_catalog.service_available_group,
            config_application_catalog.ServiceAvailableGroup)
        config.register_opt_group(
            conf, config_application_catalog.application_catalog_group,
            config_application_catalog.ApplicationCatalogGroup)
        config.register_opt_group(
            conf, config_application_catalog.service_broker_group,
            config_application_catalog.ServiceBrokerGroup)

    def get_opt_lists(self):
        return [(config_application_catalog.application_catalog_group.name,
                 config_application_catalog.ApplicationCatalogGroup),
                (config_application_catalog.service_broker_group.name,
                 config_application_catalog.ServiceBrokerGroup),
                ('service_available',
                 config_application_catalog.ServiceAvailableGroup)]
