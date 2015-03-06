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

import os
import time
import uuid

import murano.tests.functional.engine.muranomanager as core


class MuranoBase(core.MuranoTestsCore):

    @classmethod
    def setUpClass(cls):
        super(MuranoBase, cls).setUpClass()

        cls.linux = core.CONF.murano.linux_image
        cls.flavor = core.CONF.murano.standard_flavor

        cls.pkgs_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            os.path.pardir,
            'murano-app-incubator'
        ))

        cls.upload_package(
            'PostgreSQL',
            {"categories": ["Databases"], "tags": ["tag"]},
            os.path.join(cls.pkgs_path, 'io.murano.databases.PostgreSql.zip')
        )
        cls.upload_package(
            'SqlDatabase',
            {"categories": ["Databases"], "tags": ["tag"]},
            os.path.join(cls.pkgs_path, 'io.murano.databases.SqlDatabase.zip')
        )
        cls.upload_package(
            'Apache',
            {"categories": ["Application Servers"], "tags": ["tag"]},
            os.path.join(cls.pkgs_path,
                         'io.murano.apps.apache.ApacheHttpServer.zip')
        )
        cls.upload_package(
            'Tomcat',
            {"categories": ["Application Servers"], "tags": ["tag"]},
            os.path.join(cls.pkgs_path, 'io.murano.apps.apache.Tomcat.zip')
        )
        cls.upload_package(
            'Telnet',
            {"categories": ["Web"], "tags": ["tag"]},
            os.path.join(cls.pkgs_path, 'io.murano.apps.linux.Telnet.zip')
        )

    def setUp(self):
        super(MuranoBase, self).setUp()

    def tearDown(self):
        super(MuranoBase, self).tearDown()

    @classmethod
    def tearDownClass(cls):
        super(MuranoBase, cls).tearDownClass()
        cls.purge_uploaded_packages()

    def test_deploy_telnet(self):
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
                "type": "io.murano.apps.linux.Telnet",
                "id": str(uuid.uuid4())
            }
        }

        environment_name = 'Telnetenv' + uuid.uuid4().hex[:5]

        env = self._quick_deploy(environment_name, post_body)

        self.deployment_success_check(env, 23)

    def test_deploy_apache(self):
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
                "type": "io.murano.apps.apache.ApacheHttpServer",
                "id": str(uuid.uuid4())
            }
        }

        environment_name = 'Apacheenv' + uuid.uuid4().hex[:5]

        env = self._quick_deploy(environment_name, post_body)

        self.deployment_success_check(env, 80)

    def test_deploy_postgresql(self):
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
            "database": "test_db",
            "username": "test_usr",
            "password": "test_pass",
            "?": {
                "type": "io.murano.databases.PostgreSql",
                "id": str(uuid.uuid4())
            }
        }

        environment_name = 'Postgreenv' + uuid.uuid4().hex[:5]

        env = self._quick_deploy(environment_name, post_body)

        self.deployment_success_check(env, 5432)

    def test_deploy_tomcat(self):
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
                "type": "io.murano.apps.apache.Tomcat",
                "id": str(uuid.uuid4())
            }
        }

        environment_name = 'Tomcatenv' + uuid.uuid4().hex[:5]

        env = self._quick_deploy(environment_name, post_body)

        self.deployment_success_check(env, 8080)

    def test_instance_refs_are_removed_after_application_is_removed(self):
        # FIXME(sergmelikyan): Revise this as part of proper fix for #1417136
        self.skipTest('Skipped until proper fix for #1417136 is proposed')
        name = 'e' + uuid.uuid4().hex

        # create environment with telnet application
        application1 = self._get_telnet_app()
        application2 = self._get_telnet_app()
        application_id = application1['?']['id']
        instance_name = application1['instance']['name']
        apps = [application1, application2]
        environment = self._quick_deploy(name, *apps)

        # delete telnet application
        session = self.murano.sessions.configure(environment.id)
        self.murano.services.delete(environment.id,
                                    '/' + application_id,
                                    session.id)
        self.murano.sessions.deploy(environment.id, session.id)
        self.wait_for_environment_deploy(environment)

        stack_name = self._get_stack(environment.id).stack_name
        template = self.heat.stacks.template(stack_name)
        ip_addresses = '{0}-assigned-ip'.format(instance_name)
        floating_ip = '{0}-FloatingIPaddress'.format(instance_name)

        self.assertNotIn(ip_addresses, template['outputs'])
        self.assertNotIn(floating_ip, template['outputs'])
        self.assertNotIn(instance_name, template['resources'])

    def test_stack_deletion_after_env_is_deleted(self):
        name = 'e' + uuid.uuid4().hex

        application = self._get_telnet_app()
        environment = self._quick_deploy(name, application)

        stack = self._get_stack(environment.id)
        self.assertIsNotNone(stack)

        self.murano.environments.delete(environment.id)

        start_time = time.time()
        while stack is not None:
            if time.time() - start_time > 300:
                break
            time.sleep(5)
            stack = self._get_stack(environment.id)
        self.assertIsNone(stack, 'stack is not deleted')
