# Copyright (c) 2015 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from nose.plugins.attrib import attr as tag

import murano.tests.functional.common.utils as common_utils
import murano.tests.functional.integration.integration_base as core


class MistralTest(core.MistralIntegration):

    @classmethod
    def setUpClass(cls):
        super(MistralTest, cls).setUpClass()

        try:
            # Upload the Murano test package.
            cls.upload_mistral_showcase_app()

        except Exception as e:
            cls.tearDownClass()
            raise e

    @classmethod
    def tearDownClass(cls):
        with common_utils.ignored(Exception):
            cls.purge_environments()
        with common_utils.ignored(Exception):
            cls.purge_uploaded_packages()

    @tag('all', 'coverage')
    def test_deploy_package_success(self):
        # Test expects successful deployment and one output: input_1_value.

        # Create env json string.
        post_body = self._create_env_body()

        environment_name = 'Mistral_environment' + uuid.uuid4().hex[:5]

        # Deploy the environment.
        env = self.deploy_apps(environment_name, post_body)

        status = self.wait_for_final_status(env)

        self.assertIn("ready", status[0],
                      "Unexpected status : " + status[0])
        self.assertIn("input_1_value", status[1],
                      "Unexpected output value: " + status[1])
