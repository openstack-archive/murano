# Copyright (c) 2015 OpenStack Foundation, Inc.
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

import os
import uuid

from keystoneclient import exceptions as keystone_exceptions
import mistralclient.api.client as mistralclient
import testresources
import testtools

import murano.tests.functional.common.tempest_utils as tempest_utils
import murano.tests.functional.common.utils as utils


class MistralIntegration(testtools.TestCase, testtools.testcase.WithAttributes,
                         testresources.ResourcedTestCase,
                         tempest_utils.TempestDeployTestMixin):

    @classmethod
    @utils.memoize
    def mistral_client(cls):
        keystone_client = cls.keystone_client()

        endpoint_type = 'publicURL'
        service_type = 'workflowv2'

        mistral_url = keystone_client.service_catalog.url_for(
            service_type=service_type,
            endpoint_type=endpoint_type)

        auth_token = keystone_client.auth_token

        return mistralclient.client(mistral_url=mistral_url,
                                    auth_url=keystone_client.auth_url,
                                    project_id=keystone_client.tenant_id,
                                    endpoint_type=endpoint_type,
                                    service_type=service_type,
                                    auth_token=auth_token,
                                    user_id=keystone_client.user_id)

    @classmethod
    def upload_mistral_showcase_app(cls):
        app_dir = 'io.murano.apps.test.MistralShowcaseApp'
        zip_file_path = cls.zip_dir(os.path.dirname(__file__), app_dir)
        cls.init_list("_package_files")
        cls._package_files.append(zip_file_path)
        return cls.upload_package(
            'MistralShowcaseApp',
            {"categories": ["Web"], "tags": ["tag"]},
            zip_file_path)

    @staticmethod
    def _create_env_body():
        return {
            "name": "Mistral_environment",
            "?": {
                "type": "io.murano.apps.test.MistralShowcaseApp",
                "id": str(uuid.uuid4())
            }
        }


class CongressIntegration(testtools.TestCase,
                          testtools.testcase.WithAttributes,
                          testresources.ResourcedTestCase,
                          tempest_utils.TempestDeployTestMixin):

    @classmethod
    def _create_policy_req(cls, policy_name):
        return {'abbreviation': None, 'kind': None,
                'name': policy_name,
                'description': None}

    @classmethod
    def _upload_policy_enf_app(cls):
        app_dir = 'io.murano.apps.test.PolicyEnforcementTestApp'
        zip_file_path = cls.zip_dir(os.path.dirname(__file__), app_dir)
        cls.init_list("_package_files")
        cls._package_files.append(zip_file_path)
        return cls.upload_package(
            'PolicyEnforcementTestApp',
            {"categories": ["Web"], "tags": ["tag"]},
            zip_file_path)

    @classmethod
    def _create_policy(cls, policy_names, kind=None):
        for name in policy_names:
            policy_req = {"name": name}
            if kind:
                policy_req["kind"] = kind
            with utils.ignored(keystone_exceptions.Conflict):
                cls.congress_client().create_policy(policy_req)

            rules = []
            rules_file = os.path.join(
                os.path.dirname(__file__),
                "rules_" + name + ".txt")

            if os.path.isfile(rules_file):
                with open(rules_file) as f:
                    rules = [rule.strip() for rule in f.readlines()
                             if rule.strip()]
            for rule in rules:
                with utils.ignored(keystone_exceptions.Conflict):
                    cls.congress_client().create_policy_rule(name,
                                                             {'rule': rule})

    def _create_test_app(self, flavor, key):
        """Application create request body

        Deployment is expected to fail earlier due to policy violation.
        Not existing image prevents real deployment to happen
        in case that test goes wrong way.

        :param flavor: instance image flavor
        :param key: key name
        """

        return {
            "instance": {
                "flavor": flavor,
                "keyname": key,
                "image": "not_existing_image",
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": "testMurano"
            },
            "name": "teMurano",
            "?": {
                "type": "io.murano.apps.test.PolicyEnforcementTestApp",
                "id": str(uuid.uuid4())
            }
        }

    def _check_deploy_failure(self, post_body, expected_text):
        environment_name = 'PolicyEnfTestEnv' + uuid.uuid4().hex[:5]
        env = self.deploy_apps(environment_name, post_body)
        status = self.wait_for_final_status(env)
        self.assertIn("failure", status[0], "Unexpected status : " + status[0])
        self.assertIn(expected_text, status[1].lower(),
                      "Unexpected status : " + status[1])
