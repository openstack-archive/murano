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

import os
import uuid

import keystoneclient.openstack.common.apiclient.exceptions \
    as keystone_exceptions
import muranoclient.common.exceptions as murano_exceptions
import testtools

import murano.tests.functional.common.tempest_utils as tempest_utils
import murano.tests.functional.common.utils as common_utils

CONGRESS_RULES = ['invalid_flavor_name("really.bad.flavor")',
                  'predeploy_errors(eid, obj_id, msg):-'
                  'murano:objects(obj_id, eid, type),'
                  'murano:properties(obj_id, "flavor", flavor_name),'
                  'invalid_flavor_name(flavor_name),'
                  'murano:properties(obj_id, "name", obj_name),'
                  'concat(obj_name, ": bad flavor", msg)',
                  'predeploy_errors(eid, obj_id, msg):-'
                  'murano:objects(obj_id, eid, type),'
                  'murano:properties(obj_id, "keyname", key_name),'
                  'missing_key(key_name),'
                  'murano:properties(obj_id, "name", obj_name),'
                  'concat(obj_name, ": missing key", msg)',
                  'missing_key("")']


class PolicyEnforcement(testtools.TestCase,
                        tempest_utils.TempestDeployTestMixin):

    @classmethod
    def create_policy_req(cls, policy_name):
        return {'abbreviation': None, 'kind': None,
                'name': policy_name,
                'description': None}

    @classmethod
    def setUpClass(cls):
        super(PolicyEnforcement, cls).setUpClass()

        with common_utils.ignored(Exception):
            cls.congress_client().create_policy(
                cls.create_policy_req('murano_system'))
            cls.congress_client().create_policy(
                cls.create_policy_req('murano'))

        with common_utils.ignored(murano_exceptions.HTTPInternalServerError):
            cls.upload_policy_enf_app()

    @classmethod
    def tearDownClass(cls):
        cls.purge_uploaded_packages()

    @classmethod
    def upload_policy_enf_app(cls):
        app_dir = 'io.murano.apps.test.PolicyEnforcementTestApp'
        zip_file_path = cls.zip_dir(os.path.dirname(__file__), app_dir)
        cls.init_list("_package_files")
        cls._package_files.append(zip_file_path)
        return cls.upload_package(
            'PolicyEnforcementTestApp',
            {"categories": ["Web"], "tags": ["tag"]},
            zip_file_path)

    def setUp(self):
        super(PolicyEnforcement, self).setUp()
        self.rules = []

        rule_posts = [{"rule": rule} for rule in CONGRESS_RULES]
        for rule_post in rule_posts:
            with common_utils.ignored(keystone_exceptions.Conflict):
                self.rules.append(self.congress_client().create_policy_rule(
                    'murano_system',
                    rule_post))

    def tearDown(self):
        super(PolicyEnforcement, self).tearDown()
        self.purge_environments()

        for rule in self.rules:
            self.congress_client().delete_policy_rule(
                "murano_system", rule["id"])

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

    def test_deploy_policy_fail_flavor(self):
        """Test expects failure due to blacklisted flavor."""

        self._check_deploy_failure(
            self._create_test_app(flavor="really.bad.flavor",
                                  key="test-key"),
            "bad flavor")

    def test_deploy_policy_fail_key(self):
        """Test expects failure due to empty key name."""

        self._check_deploy_failure(
            self._create_test_app(key="",
                                  flavor="m1.small"),
            "missing key")
