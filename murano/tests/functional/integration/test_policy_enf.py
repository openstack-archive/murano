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
from nose.plugins.attrib import attr as tag

import murano.tests.functional.common.utils as common_utils
import murano.tests.functional.integration.integration_base as core


class PolicyEnforcementTest(core.CongressIntegration):

    @classmethod
    def setUpClass(cls):
        super(PolicyEnforcementTest, cls).setUpClass()

        cls._create_policy(["murano", "murano_system"])
        cls._create_policy(["murano_action"], kind="action")

        with common_utils.ignored(murano_exceptions.HTTPInternalServerError):
            cls._upload_policy_enf_app()

    @classmethod
    def tearDownClass(cls):
        cls.purge_uploaded_packages()

    def tearDown(self):
        super(PolicyEnforcementTest, self).tearDown()
        self.purge_environments()

    @tag('all', 'coverage')
    def test_deploy_policy_fail_key(self):
        """Test expects failure due to empty key name.

        In rules_murano_system.txt file are defined congress
        rules preventing deploy environment where instances
        have empty keyname property. In other words admin
        prevented spawn instance without assigned key pair.
        """

        self._check_deploy_failure(
            self._create_test_app(key='',
                                  flavor='m1.small'),
            'missing key')

    @tag('all', 'coverage')
    def test_deploy_policy_fail_flavor(self):
        """Test expects failure due to blacklisted flavor

        In rules_murano_system.txt file are defined congress
        rules preventing deploy environment where instances
        have flavor property set to 'really.bad.flavor'.
        """

        self._check_deploy_failure(
            self._create_test_app(flavor='really.bad.flavor',
                                  key='test-key'),
            'bad flavor')

    @tag('all', 'coverage')
    def test_set_property_policy(self):
        """Tests environment modification by policy

        In rules_murano_system.txt file are defined congress
        rules changing flavor property. There are defined
        synonyms for 'really.bad.flavor'. One of such synonyms
        is 'horrible.flavor' Environment is modified prior deployment.
        The synonym name 'horrible.flavor' is set to original
        value 'really.bad.flavor' and then deployment is aborted
        because instances of 'really.bad.flavor' are prevented
        to be deployed like for the test above.
        """

        self._check_deploy_failure(
            self._create_test_app(key="test-key",
                                  flavor="horrible.flavor"),
            "bad flavor")
