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

import muranoclient.common.exceptions as murano_exceptions

import murano.tests.functional.common.utils as common_utils
import murano.tests.functional.engine.integration_base as core


class PolicyEnforcement(core.CongressIntegration):

    @classmethod
    def setUpClass(cls):
        super(PolicyEnforcement, cls).setUpClass()

        cls._create_policy(["murano", "murano_system"])
        cls._create_policy(["murano_action"], kind="action")

        with common_utils.ignored(murano_exceptions.HTTPInternalServerError):
            cls._upload_policy_enf_app()

    @classmethod
    def tearDownClass(cls):
        cls.purge_uploaded_packages()

    def tearDown(self):
        super(PolicyEnforcement, self).tearDown()
        self.purge_environments()

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
