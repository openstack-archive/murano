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
import socket
import time
import urlparse
import uuid

import requests
import testresources
import testtools

from heatclient import client as heatclient
from keystoneclient.v2_0 import client as ksclient

import murano.tests.functional.engine.config as cfg


CONF = cfg.cfg.CONF


class Client(object):
    def __init__(self, user, password, tenant, auth_url, murano_url):
        self.auth = ksclient.Client(
            username=user, password=password,
            tenant_name=tenant, auth_url=auth_url
        )
        self.endpoint = urlparse.urljoin(murano_url, 'v1/')
        self.headers = {
            'X-Auth-Token': self.auth.auth_token,
            'Content-type': 'application/json'
        }

    def get_url(self, url_part=None):
        return urlparse.urljoin(self.endpoint, url_part)

    def create_environment(self, name):
        endpoint = self.get_url('environments')
        body = json.dumps({'name': name})

        return requests.post(endpoint, data=body, headers=self.headers).json()

    def delete_environment(self, environment_id, timeout=180):
        endpoint = self.get_url('environments/%s' % environment_id)

        def _is_exist():
            resp = requests.get(endpoint, headers=self.headers)
            return resp.status_code == requests.codes.ok

        env_deleted = not _is_exist()
        requests.delete(endpoint, headers=self.headers)

        start_time = time.time()
        while env_deleted is not True:
            if timeout and time.time() - start_time > timeout:
                raise Exception('Environment was not deleted')
            time.sleep(5)
            env_deleted = not _is_exist()

    def get_environment(self, environment_id):
        endpoint = self.get_url('environments/%s' % environment_id)
        return requests.get(endpoint, headers=self.headers).json()

    def create_session(self, environment_id):
        endpoint = self.get_url('environments/%s/configure' % environment_id)
        return requests.post(endpoint, headers=self.headers).json()

    def deploy_session(self, environment_id, session_id):
        endpoint = self.get_url('environments/{0}/sessions/{1}/deploy'.format(
            environment_id, session_id))
        return requests.post(endpoint, headers=self.headers)

    def create_service(self, environment_id, session_id, json_data):
        endpoint = self.get_url('environments/%s/services' % environment_id)
        body = json.dumps(json_data)
        headers = self.headers.copy()
        headers['x-configuration-session'] = session_id

        return requests.post(endpoint, data=body, headers=headers).json()

    def delete_service(self, environment_id, session_id, service_id):
        endpoint = self.get_url('environments/{0}/services/{1}'.format(
            environment_id, service_id
        ))
        headers = self.headers.copy()
        headers['x-configuration-session'] = session_id

        requests.delete(endpoint, headers=headers)

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
        endpoint = self.get_url('environments/%s/deployments' % environment_id)
        response = requests.get(endpoint, headers=self.headers)
        return response.json()['deployments']

    def upload_package(self, name, package, description):
        endpoint = self.get_url('catalog/packages')
        body = {'JsonString': json.dumps(description)}
        files = {name: open(package, 'rb')}
        headers = self.headers.copy()
        del headers['Content-type']

        resp = requests.post(endpoint, data=body, files=files, headers=headers)
        return resp.json()['id']


class MuranoBase(testtools.TestCase, testtools.testcase.WithAttributes,
                 testresources.ResourcedTestCase):

    @classmethod
    def setUpClass(cls):
        super(MuranoBase, cls).setUpClass()

        cfg.load_config()

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

        cls.pkgs_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            os.path.pardir,
            'murano-app-incubator'
        ))

        cls.postgre_id = cls.client.upload_package(
            'PostgreSQL',
            os.path.join(cls.pkgs_path, 'io.murano.apps.PostgreSql.zip'),
            {'categories': ['Databases'], 'tags': ['tag']}
        )
        cls.apache_id = cls.client.upload_package(
            'Apache',
            os.path.join(cls.pkgs_path, 'io.murano.apps.apache.Apache.zip'),
            {'categories': ['Application Servers'], 'tags': ['tag']}
        )
        cls.tomcat_id = cls.client.upload_package(
            'Tomcat',
            os.path.join(cls.pkgs_path, 'io.murano.apps.apache.Tomcat.zip'),
            {'categories': ['Application Servers'], 'tags': ['tag']}
        )
        cls.telnet_id = cls.client.upload_package(
            'Telnet',
            os.path.join(cls.pkgs_path, 'io.murano.apps.linux.Telnet.zip'),
            {'categories': ['Web'], 'tags': ['tag']}
        )
        cls.ad_id = cls.client.upload_package(
            'Active Directory',
            os.path.join(cls.pkgs_path,
                         'io.murano.windows.ActiveDirectory.zip'),
            {'categories': ['Microsoft Services'], 'tags': ['tag']}
        )

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

    def deployment_success_check(self, environment, port):
        deployments = self.client.deployments_list(environment['id'])

        for deployment in deployments:
            msg = 'Deployment status is %s' % deployment['state']
            self.assertEqual('success', deployment['state'], msg)

        instance = environment['services'][0]['instance']
        self.assertTrue(instance['floatingIpAddress'])
        self.check_port_access(instance['floatingIpAddress'], port)

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

        session = self.client.create_session(environment['id'])

        self.client.create_service(environment['id'], session['id'], post_body)
        self.client.deploy_session(environment['id'], session['id'])

        env = self.client.wait_for_environment_deploy(environment['id'])
        self.assertIsNotNone(env)

        self.deployment_success_check(env, 23)

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

        self.deployment_success_check(env, 80)

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

        self.deployment_success_check(env, 5432)

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

        session = self.client.create_session(environment['id'])

        self.client.create_service(environment['id'], session['id'], post_body)
        self.client.deploy_session(environment['id'], session['id'])

        env = self.client.wait_for_environment_deploy(environment['id'])
        self.assertIsNotNone(env)

        self.deployment_success_check(env, 8080)

    def _get_telnet_app(self):
        return {
            "instance": {
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "flavor": "m1.medium",
                "image": self.linux,
                "name": "instance{0}".format(uuid.uuid4().hex[:5]),
            },
            "name": "app{0}".format(uuid.uuid4().hex[:5]),
            "?": {
                "type": "io.murano.apps.linux.Telnet",
                "id": str(uuid.uuid4())
            }
        }

    def _quick_deploy(self, name, *apps):
        environment = self.client.create_environment(name)
        session = self.client.create_session(environment['id'])
        environment_id, session_id = environment['id'], session['id']

        for app in apps:
            self.client.create_service(environment_id, session_id, app)
        self.client.deploy_session(environment_id, session_id)
        return self.client.wait_for_environment_deploy(environment_id)

    def _get_stack(self, environment_id):

        for stack in self.heat_client.stacks.list():
            if environment_id in stack.description:
                return stack

    def test_instance_refs_are_removed_after_application_is_removed(self):
        # FIXME(sergmelikyan): Revise this as part of proper fix for #1359998
        self.skipTest('Skipped until proper fix for #1359998 is proposed')

        name = 'e' + uuid.uuid4().hex

        # create environment with telnet application
        application1 = self._get_telnet_app()
        application2 = self._get_telnet_app()
        application_id = application1['?']['id']
        instance_name = application1['instance']['name']
        apps = [application1, application2]
        environment_id = self._quick_deploy(name, *apps)['id']
        # add environment to the list for tear-down clean-up
        self.environments.append(environment_id)

        # delete telnet application
        session_id = self.client.create_session(environment_id)['id']
        self.client.delete_service(environment_id, session_id, application_id)
        self.client.deploy_session(environment_id, session_id)
        self.client.wait_for_environment_deploy(environment_id)

        stack_name = self._get_stack(environment_id).stack_name
        template = self.heat_client.stacks.template(stack_name)
        ip_addresses = '{0}-assigned-ip'.format(instance_name)
        floating_ip = '{0}-FloatingIPaddress'.format(instance_name)

        self.assertNotIn(ip_addresses, template['outputs'])
        self.assertNotIn(floating_ip, template['outputs'])
        self.assertNotIn(instance_name, template['resources'])

    def test_stack_deletion_after_env_is_deleted(self):
        name = 'e' + uuid.uuid4().hex

        application = self._get_telnet_app()
        environment = self._quick_deploy(name, application)
        self.assertIsNotNone(environment)

        stack = self._get_stack(environment['id'])
        self.assertIsNotNone(stack)

        self.client.delete_environment(environment['id'])

        start_time = time.time()
        while stack is not None:
            if time.time() - start_time > 300:
                break
            time.sleep(5)
            stack = self._get_stack(environment['id'])
        self.assertIsNone(stack, 'stack is not deleted')
