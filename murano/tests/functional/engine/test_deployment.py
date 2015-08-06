# Copyright (c) 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from nose.plugins.attrib import attr as tag

import murano.tests.functional.engine.manager as core


class MuranoDeploymentTest(core.MuranoTestsCore):

    @classmethod
    def setUpClass(cls):
        super(MuranoDeploymentTest, cls).setUpClass()

        cls.linux = core.CONF.murano.linux_image
        cls.flavor = core.CONF.murano.standard_flavor

        cls.upload_app('io.murano.apps.test.UpdateExecutor',
                       'UpdateExecutor',
                       {"categories": ["Web"], "tags": ["tag"]})

    @classmethod
    def tearDownClass(cls):
        super(MuranoDeploymentTest, cls).tearDownClass()

        cls.purge_environments()
        cls.purge_uploaded_packages()

    @tag('gate', 'all', 'coverage')
    def test_app_deployment(self):
        post_body = {
            "instance": {
                "flavor": self.flavor,
                "image": self.linux,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": "testMurano"
            },
            "name": "teMurano",
            "?": {
                "type": "io.murano.apps.test.UpdateExecutor",
                "id": str(uuid.uuid4())
            }
        }

        environment_name = self.rand_name('dummyMurano')
        environment = self.create_environment(name=environment_name)
        session = self.create_session(environment)
        self.add_service(environment, post_body, session)
        self.deploy_environment(environment, session)
        self.wait_for_environment_deploy(environment)
