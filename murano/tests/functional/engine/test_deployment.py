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

        cls.upload_app('io.murano.apps.test.Lighttpd',
                       'Lighttpd',
                       {"categories": ["Web"], "tags": ["tag"]})

        cls.upload_app('io.murano.apps.test.ApacheHttpServerCustom',
                       'Apache HTTP Server Custom',
                       {"categories": ["Web"], "tags": ["test"]})

    @classmethod
    def tearDownClass(cls):
        super(MuranoDeploymentTest, cls).tearDownClass()

        cls.purge_environments()
        cls.purge_uploaded_packages()

    @tag('gate', 'all', 'coverage')
    def test_app_deployment(self):
        post_body = self.get_test_app()
        environment_name = self.rand_name('dummyMurano')
        environment = self.create_environment(name=environment_name)
        session = self.create_session(environment)
        self.add_service(environment, post_body, session)
        self.deploy_environment(environment, session)

    @tag('gate', 'all', 'coverage')
    def test_resources_deallocation(self):
        app_1 = self.get_test_app()
        app_2 = self.get_test_app()
        environment_name = self.rand_name('dummyMurano')
        environment = self.create_environment(name=environment_name)
        session = self.create_session(environment)
        self.add_service(environment, app_1, session)
        self.add_service(environment, app_2, session)
        self.deploy_environment(environment, session)

        environment = self.get_environment(environment)
        app_for_remove = self.get_service(environment, app_1['name'],
                                          to_dict=False)
        session = self.create_session(environment)
        environment = self.delete_service(environment, session, app_for_remove)
        self.deploy_environment(environment, session)

        instance_name = app_1['instance']['name']
        stack = self._get_stack(environment.id)
        template = self.get_stack_template(stack)
        ip_addresses = '{0}-assigned-ip'.format(instance_name)
        floating_ip = '{0}-FloatingIPaddress'.format(instance_name)

        self.assertNotIn(ip_addresses, template['outputs'])
        self.assertNotIn(floating_ip, template['outputs'])
        self.assertNotIn(instance_name, template['resources'])

    @tag('gate', 'all', 'coverage')
    def test_dependent_apps(self):
        post_body = self.get_test_app()
        environment_name = self.rand_name('dummyMurano')
        environment = self.create_environment(name=environment_name)
        session = self.create_session(environment)
        updater = self.add_service(environment, post_body, session,
                                   to_dict=True)
        post_body = {
            "name": self.rand_name("lighttest"),
            "updater": updater,
            "?": {
                "type": "io.murano.apps.test.Lighttpd",
                "id": str(uuid.uuid4())
            }
        }
        self.add_service(environment, post_body, session)
        self.deploy_environment(environment, session)
        self.status_check(environment,
                          [[updater['instance']['name'], 22, 80]])

    @tag('gate', 'all', 'coverage')
    def test_simple_software_configuration(self):
        post_body = {
            "instance": {
                "flavor": self.flavor,
                "image": self.linux,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": self.rand_name("mrn-test"),
            },
            "name": self.rand_name("ssc-test"),
            "userName": self.rand_name("user"),
            "?": {
                "type": "io.murano.apps.test.ApacheHttpServerCustom",
                "id": str(uuid.uuid4())
            }
        }
        username = post_body["userName"]
        environment_name = self.rand_name('SSC-murano')
        environment = self.create_environment(name=environment_name)
        session = self.create_session(environment)
        self.add_service(environment, post_body, session, to_dict=True)
        self.deploy_environment(environment, session)
        self.status_check(environment,
                          [[post_body['instance']['name'], 22, 80]])
        resp = self.check_path(environment, '', post_body['instance']['name'])
        self.assertIn(username, resp.text, "Required information not found in "
                                           "response from server")
