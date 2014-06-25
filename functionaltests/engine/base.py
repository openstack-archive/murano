# Copyright (c) 2014 Mirantis, Inc.
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

import json
import os
import requests
import socket
import testresources
import testtools
import time
import uuid

from heatclient import client as heatclient
from keystoneclient.v2_0 import client as ksclient

import functionaltests.engine.config as cfg


CONF = cfg.cfg.CONF


class Client(object):

    def __init__(self, user, password, tenant, auth_url, murano_url):

        self.auth = ksclient.Client(username=user, password=password,
                                    tenant_name=tenant, auth_url=auth_url)

        self.endpoint = murano_url

        self.headers = {
            'X-Auth-Token': self.auth.auth_token,
            'Content-type': 'application/json'
        }

    def create_environment(self, name):
        post_body = {'name': name}
        resp = requests.post(self.endpoint + 'environments',
                             data=json.dumps(post_body),
                             headers=self.headers)

        return resp.json()

    def delete_environment(self, environment_id):
        endpoint = '{0}environments/{1}'.format(self.endpoint, environment_id)
        return requests.delete(endpoint, headers=self.headers)

    def get_environment(self, environment_id):
        return requests.get('{0}environments/{1}'.format(self.endpoint,
                                                         environment_id),
                            headers=self.headers).json()

    def create_session(self, environment_id):
        post_body = None
        endpoint = '{0}environments/{1}/configure'.format(self.endpoint,
                                                          environment_id)

        return requests.post(endpoint, data=post_body,
                             headers=self.headers).json()

    def deploy_session(self, environment_id, session_id):
        endpoint = '{0}environments/{1}/sessions/{2}/deploy'.format(
            self.endpoint, environment_id, session_id)

        return requests.post(endpoint, data=None, headers=self.headers)

    def create_service(self, environment_id, session_id, json_data):
        headers = self.headers.copy()
        headers.update({'x-configuration-session': session_id})

        endpoint = '{0}environments/{1}/services'.format(self.endpoint,
                                                         environment_id)

        return requests.post(endpoint, data=json.dumps(json_data),
                             headers=headers).json()

    def wait_for_environment_deploy(self, environment_id):
        environment = self.get_environment(environment_id)

        start_time = time.time()

        while environment['status'] != 'ready':
            if time.time() - start_time > 1200:
                return
            time.sleep(5)
            environment = self.get_environment(environment_id)

        return environment

    def get_ip_list(self, environment):
        return [service['instance']['ipAddresses']
                for service in environment['services']]

    def deployments_list(self, environment_id):
        endpoint = '{0}environments/{1}/deployments'.format(self.endpoint,
                                                            environment_id)

        return requests.get(endpoint,
                            headers=self.headers).json()['deployments']


class MuranoBase(testtools.TestCase, testtools.testcase.WithAttributes,
                 testresources.ResourcedTestCase):

    @classmethod
    def setUpClass(cls):
        super(MuranoBase, cls).setUpClass()

        cls.client = Client(user=CONF.murano.user,
                            password=CONF.murano.password,
                            tenant=CONF.murano.tenant,
                            auth_url=CONF.murano.auth_url,
                            murano_url=CONF.murano.murano_url)

        cls.linux = CONF.murano.linux_image
        cls.windows = CONF.murano.windows_image

        heat_url = cls.client.auth.service_catalog.url_for(
            service_type='orchestration', endpoint_type='publicURL')

        cls.heat_client = heatclient.Client('1', endpoint=heat_url,
                                            token=cls.client.auth.auth_token)

        cls.location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))

        cls.packages_path = '/'.join(cls.location.split('/')[:-1:])

        def upload_package(package_name, body, app):
            files = {'%s' % package_name: open(
                os.path.join(cls.packages_path, app), 'rb')}

            post_body = {'JsonString': json.dumps(body)}
            request_url = '{endpoint}{url}'.format(
                endpoint=CONF.murano.murano_url,
                url='catalog/packages')

            headers = cls.client.headers.copy()
            del headers['Content-type']

            return requests.post(request_url,
                                 files=files,
                                 data=post_body,
                                 headers=headers).json()['id']

        cls.postgre_id = upload_package(
            'PostgreSQL',
            {"categories": ["Databases"], "tags": ["tag"]},
            'murano-app-incubator/io.murano.apps.PostgreSql.zip')
        cls.apache_id = upload_package(
            'Apache',
            {"categories": ["Application Servers"], "tags": ["tag"]},
            'murano-app-incubator/io.murano.apps.apache.Apache.zip')
        cls.tomcat_id = upload_package(
            'Tomcat',
            {"categories": ["Application Servers"], "tags": ["tag"]},
            'murano-app-incubator/io.murano.apps.apache.Tomcat.zip')
        cls.telnet_id = upload_package(
            'Telnet',
            {"categories": ["Web"], "tags": ["tag"]},
            'murano-app-incubator/io.murano.apps.linux.Telnet.zip')
        cls.ad_id = upload_package(
            'Active Directory',
            {"categories": ["Microsoft Services"], "tags": ["tag"]},
            'murano-app-incubator/io.murano.windows.ActiveDirectory.zip')

    def setUp(self):
        super(MuranoBase, self).setUp()

        self.environments = []
        self.stack_names = []

    def tearDown(self):
        super(MuranoBase, self).tearDown()

        for env in self.environments:
            try:
                self.client.delete_environment(env)
            except Exception:
                pass

        # add workaround for https://bugs.launchpad.net/murano/+bug/1330966
        time.sleep(60)

        stack_list = self.heat_client.stacks.list()
        for stack_name in self.stack_names:
            try:
                for stack in stack_list:
                    if stack.stack_name == stack_name:
                        self.heat_client.stacks.delete(stack.id)
            except Exception:
                pass

    def check_port_access(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        result = sock.connect_ex((str(ip), port))
        sock.close()

        self.assertEqual(0, result)

    def deployment_success_check(self, env_id, ip, port):
        deployments = self.client.deployments_list(env_id)

        for deployment in deployments:
            self.assertEqual('success', deployment['state'])

        self.check_port_access(ip, port)

    def test_deploy_telnet(self):
        post_body = {
            "instance": {
                "flavor": "m1.medium",
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

        environment = self.client.create_environment(environment_name)
        self.environments.append(environment['id'])
        self.stack_names.append(environment_name)

        session = self.client.create_session(environment['id'])

        self.client.create_service(environment['id'], session['id'], post_body)
        self.client.deploy_session(environment['id'], session['id'])

        env = self.client.wait_for_environment_deploy(environment['id'])

        self.assertIsNotNone(env)

        ip_list = self.client.get_ip_list(env)

        self.deployment_success_check(environment['id'], ip_list[0][1], 23)

    def test_deploy_apache(self):
        post_body = {
            "instance": {
                "flavor": "m1.medium",
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
                "type": "io.murano.apps.apache.Apache",
                "id": str(uuid.uuid4())
            }
        }

        environment_name = 'Apacheenv' + uuid.uuid4().hex[:5]

        environment = self.client.create_environment(environment_name)
        self.environments.append(environment['id'])
        self.stack_names.append(environment_name)

        session = self.client.create_session(environment['id'])

        self.client.create_service(environment['id'], session['id'], post_body)
        self.client.deploy_session(environment['id'], session['id'])

        env = self.client.wait_for_environment_deploy(environment['id'])

        self.assertIsNotNone(env)

        ip_list = self.client.get_ip_list(env)

        self.deployment_success_check(environment['id'], ip_list[0][1], 80)

    def test_deploy_postgresql(self):
        post_body = {
            "instance": {
                "flavor": "m1.medium",
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
                "type": "io.murano.apps.PostgreSql",
                "id": str(uuid.uuid4())
            }
        }

        environment_name = 'Postgreenv' + uuid.uuid4().hex[:5]

        environment = self.client.create_environment(environment_name)
        self.environments.append(environment['id'])
        self.stack_names.append(environment_name)

        session = self.client.create_session(environment['id'])

        self.client.create_service(environment['id'], session['id'], post_body)
        self.client.deploy_session(environment['id'], session['id'])

        env = self.client.wait_for_environment_deploy(environment['id'])

        self.assertIsNotNone(env)

        ip_list = self.client.get_ip_list(env)

        self.deployment_success_check(environment['id'], ip_list[0][1], 5432)

    def test_deploy_tomcat(self):
        post_body = {
            "instance": {
                "flavor": "m1.medium",
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

        environment = self.client.create_environment(environment_name)
        self.environments.append(environment['id'])
        self.stack_names.append(environment_name)

        session = self.client.create_session(environment['id'])

        self.client.create_service(environment['id'], session['id'], post_body)
        self.client.deploy_session(environment['id'], session['id'])

        env = self.client.wait_for_environment_deploy(environment['id'])

        self.assertIsNotNone(env)

        ip_list = self.client.get_ip_list(env)

        self.deployment_success_check(environment['id'], ip_list[0][1], 8080)
