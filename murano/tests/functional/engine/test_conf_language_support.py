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

import murano.tests.functional.common.utils as common_utils
import murano.tests.functional.engine.manager as core
from nose.plugins.attrib import attr as tag


class LanguageSupportTest(core.MuranoTestsCore):

    @classmethod
    def setUpClass(cls):
        super(LanguageSupportTest, cls).setUpClass()
        cls.linux = core.CONF.murano.linux_image
        cls.flavor = core.CONF.murano.standard_flavor
        cls.keyname = core.CONF.murano.keyname
        cls.instance_type = core.CONF.murano.instance_type

        try:
            # Upload the Murano test package.
            cls.upload_app('io.murano.conflang.chef.ExampleChef',
                           'ExampleChef', {"tags": ["tag"]})
            cls.upload_app('io.murano.conflang.puppet.ExamplePuppet',
                           'ExamplePuppet', {"tags": ["tag"]})
        except Exception as e:
            cls.tearDownClass()
            raise e

    @classmethod
    def tearDownClass(cls):
        with common_utils.ignored(Exception):
            try:
                cls.purge_uploaded_packages()
            except Exception as e:
                raise e

    def _test_deploy(self, environment_name, package_name, port):
        post_body = {
            "instance": {
                "flavor": self.flavor,
                "image": self.linux,
                "keyname": self.keyname,
                "assignFloatingIp": True,
                'name': environment_name,
                "?": {
                    "type": "io.murano.resources.ConfLangInstance",
                    "id": str(uuid.uuid4())
                },
            },
            "name": environment_name,
            "port": port,
            "?": {
                "type": package_name,
                "id": str(uuid.uuid4())
            }
        }

        environment_name = environment_name + uuid.uuid4().hex[:5]
        environment = self.create_environment(name=environment_name)
        session = self.create_session(environment)
        self.add_service(environment, post_body, session)
        self.deploy_environment(environment, session)
        self.wait_for_environment_deploy(environment)
        self.deployment_success_check(environment, port)

    @tag('gate', 'all', 'coverage')
    def test_deploy_example_chef_example(self):
        self._test_deploy('chefExample',
                          'io.murano.conflang.chef.ExampleChef', 22)

    @tag('gate', 'all', 'coverage')
    def test_deploy_example_puppet_example(self):
        self._test_deploy('puppetExample',
                          "io.murano.conflang.puppet.ExamplePuppet", 22)
