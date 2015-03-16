# Copyright (c) 2015 Mirantis, Inc.
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


import json
import random
import socket
import time
import uuid

import requests
import testresources
import testtools
import yaml

import murano.tests.functional.common.utils as utils
import murano.tests.functional.engine.config as cfg


CONF = cfg.cfg.CONF


class MuranoTestsCore(testtools.TestCase, testtools.testcase.WithAttributes,
                      testresources.ResourcedTestCase, utils.DeployTestMixin):
    """This manager provides access to Murano-api service."""
    @classmethod
    def setUpClass(cls):
        super(MuranoTestsCore, cls).setUpClass()

        cfg.load_config()
        cls.keystone = cls.keystone_client()
        cls.murano_url = cls.get_murano_url()
        cls.heat_url = cls.heat_client()
        cls.murano_endpoint = cls.murano_url + '/v1/'
        cls.murano = cls.murano_client()
        cls._environments = []

    def setUp(self):
        super(MuranoTestsCore, self).setUp()
        self.keystone = self.keystone_client()
        self.heat = self.heat_client()
        self.murano = self.murano_client()
        self.headers = {'X-Auth-Token': self.murano.auth_token,
                        'content-type': 'application/json'}

    def tearDown(self):
        super(MuranoTestsCore, self).tearDown()
        self.purge_environments()

    def rand_name(self, name='murano_env'):
        return name + str(random.randint(1, 0x7fffffff))

    def wait_for_environment_deploy(self, environment):
        start_time = time.time()
        status = environment.manager.get(environment.id).status
        while status != 'ready':
            status = environment.manager.get(environment.id).status
            if time.time() - start_time > 3000:
                self.fail(
                    'Environment deployment is not finished in 1200 seconds')
            elif status == 'deploy failure':
                self.fail('Environment has incorrect status '
                          '{0}'.format(status))
            time.sleep(5)

        return environment.manager.get(environment.id)

    def check_port_access(self, ip, port):
        result = 1
        start_time = time.time()
        while time.time() - start_time < 300:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((str(ip), port))
            sock.close()

            if result == 0:
                break
            time.sleep(5)

        self.assertEqual(0, result, '%s port is closed on instance' % port)

    def deployment_success_check(self, environment, *ports):
        deployment = self.murano.deployments.list(environment.id)[-1]

        self.assertEqual('success', deployment.state,
                         'Deployment status is {0}'.format(deployment.state))

        ip = environment.services[0]['instance']['floatingIpAddress']

        if ip:
            for port in ports:
                self.check_port_access(ip, port)
        else:
            self.fail('Instance does not have floating IP')

    def create_env(self):
        name = self.rand_name('MuranoTe')
        environment = self.murano.environments.create({'name': name})
        self._environments.append(environment)
        return environment

    def create_session(self, environment):
        return self.murano.sessions.configure(environment.id)

    def delete_session(self, environment, session):
        return self.murano.sessions.delete(environment.id, session.id)

    def add_service(self, environment, data, session):
        """This function adding a specific service to environment
        Returns specific class <Service>
        :param environment:
        :param data:
        :param session:
        :return:
        """
        return self.murano.services.post(environment.id,
                                         path='/', data=data,
                                         session_id=session.id)

    def create_service(self, environment, session, json_data):
        """This function adding a specific service to environment
        Returns a JSON object with a service
        :param environment:
        :param session:
        :param json_data:
        :return:
        """
        headers = self.headers.copy()
        headers.update({'x-configuration-session': session.id})
        endpoint = '{0}environments/{1}/services'.format(self.murano_endpoint,
                                                         environment.id)
        return requests.post(endpoint, data=json.dumps(json_data),
                             headers=headers).json()

    def deploy_environment(self, environment, session):
        self.murano.sessions.deploy(environment.id, session.id)
        return self.wait_for_environment_deploy(environment)

    def get_environment(self, environment):
        return self.murano.environments.get(environment.id)

    def get_service_as_json(self, environment):
        service = self.murano.services.list(environment.id)[0]
        service = service.to_dict()
        service = json.dumps(service)
        return yaml.load(service)

    def _quick_deploy(self, name, *apps):
        environment = self.murano.environments.create({'name': name})
        self._environments.append(environment)

        session = self.murano.sessions.configure(environment.id)

        for app in apps:
            self.murano.services.post(environment.id,
                                      path='/',
                                      data=app,
                                      session_id=session.id)

        self.murano.sessions.deploy(environment.id, session.id)

        return self.wait_for_environment_deploy(environment)

    def _get_stack(self, environment_id):

        for stack in self.heat.stacks.list():
            if environment_id in stack.description:
                return stack

    def _get_telnet_app(self):
        return {
            "instance": {
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "flavor": self.flavor,
                "image": self.linux,
                "name": "instance{0}".format(uuid.uuid4().hex[:5]),
            },
            "name": "app{0}".format(uuid.uuid4().hex[:5]),
            "?": {
                "type": "io.murano.apps.linux.Telnet",
                "id": str(uuid.uuid4())
            }
        }
