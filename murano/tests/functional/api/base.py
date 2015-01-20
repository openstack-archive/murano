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
import time
import uuid

import requests

from tempest import clients
from tempest.common import isolated_creds
from tempest import config
from tempest import test
from tempest_lib.common import rest_client
from tempest_lib import exceptions


CONF = config.CONF


class MuranoClient(rest_client.RestClient):
    def __init__(self, auth_provider):
        super(MuranoClient, self).__init__(
            auth_provider,
            'application_catalog',
            CONF.identity.region
        )

    def get_environments_list(self):
        resp, body = self.get('v1/environments')

        return resp, json.loads(body)

    def create_environment(self, name):
        post_body = '{"name": "%s"}' % name

        resp, body = self.post('v1/environments', post_body)

        return resp, json.loads(body)

    def delete_environment(self, environment_id, timeout=180):
        def _is_exist():
            try:
                resp, _ = self.get('v1/environments/{0}'.format(
                    environment_id))
            except exceptions.NotFound:
                return False
            return resp.status == 200

        env_deleted = not _is_exist()
        self.delete('v1/environments/{0}'.format(environment_id))

        start_time = time.time()
        while env_deleted is not True:
            if timeout and time.time() - start_time > timeout:
                raise Exception('Environment was not deleted')
            time.sleep(5)
            env_deleted = not _is_exist()

    def update_environment(self, environment_id):
        post_body = '{"name": "%s"}' % ("changed-environment-name")

        resp, body = self.put('v1/environments/{0}'.format(environment_id),
                              post_body)

        return resp, json.loads(body)

    def get_environment(self, environment_id):
        resp, body = self.get('v1/environments/{0}'.format(environment_id))

        return resp, json.loads(body)

    def create_session(self, environment_id):
        post_body = None

        resp, body = self.post(
            'v1/environments/{0}/configure'.format(environment_id),
            post_body
        )

        return resp, json.loads(body)

    def delete_session(self, environment_id, session_id):
        return self.delete(
            'v1/environments/{0}/sessions/{1}'.format(environment_id,
                                                      session_id))

    def get_session(self, environment_id, session_id):
        resp, body = self.get(
            'v1/environments/{0}/sessions/{1}'.format(environment_id,
                                                      session_id))

        return resp, json.loads(body)

    def deploy_session(self, environment_id, session_id):
        post_body = None
        url = 'v1/environments/{0}/sessions/{1}/deploy'
        resp, body = self.post(url.format(environment_id, session_id),
                               post_body)

        return resp, json.loads(body)

    def create_service(self, environment_id, session_id, post_body):
        post_body = json.dumps(post_body)

        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )

        resp, body = self.post(
            'v1/environments/{0}/services'.format(environment_id),
            post_body,
            headers
        )

        return resp, json.loads(body)

    def delete_service(self, environment_id, session_id, service_id):
        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )

        return self.delete(
            'v1/environments/{0}/services/{1}'.format(environment_id,
                                                      service_id),
            headers
        )

    def get_services_list(self, environment_id, session_id):
        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )

        resp, body = self.get(
            'v1/environments/{0}/services'.format(environment_id),
            headers
        )

        return resp, json.loads(body)

    def get_service(self, environment_id, session_id, service_id):
        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )

        resp, body = self.get(
            'v1/environments/{0}/services/{1}'.format(environment_id,
                                                      service_id),
            headers
        )

        return resp, json.loads(body)

    def get_list_packages(self):
        resp, body = self.get('v1/catalog/packages')

        return resp, json.loads(body)

    def get_package(self, id):
        resp, body = self.get('v1/catalog/packages/{0}'.format(id))

        return resp, json.loads(body)

    def upload_package(self, package_name, body):
        __location__ = os.path.realpath(os.path.join(
            os.getcwd(), os.path.dirname(__file__)))

        headers = {'X-Auth-Token': self.auth_provider.get_token()}

        files = {'%s' % package_name: open(
            os.path.join(__location__, 'v1/DummyTestApp.zip'), 'rb')}

        post_body = {'JsonString': json.dumps(body)}
        request_url = '{endpoint}{url}'.format(endpoint=self.base_url,
                                               url='/v1/catalog/packages')

        resp = requests.post(request_url, files=files, data=post_body,
                             headers=headers)

        return resp

    def update_package(self, id, post_body):
        headers = {
            'X-Auth-Token': self.auth_provider.get_token(),
            'content-type': 'application/murano-packages-json-patch'
        }

        resp, body = self.patch('v1/catalog/packages/{0}'.format(id),
                                json.dumps(post_body), headers=headers)

        return resp, json.loads(body)

    def delete_package(self, id):
        return self.delete('v1/catalog/packages/{0}'.format(id))

    def download_package(self, id):
        return self.get('v1/catalog/packages/{0}/download'.format(id))

    def get_ui_definition(self, id):
        return self.get('v1/catalog/packages/{0}/ui'.format(id))

    def get_logo(self, id):
        return self.get('v1/catalog/packages/{0}/logo'.format(id))

    def list_categories(self):
        resp, body = self.get('v1/catalog/packages/categories')

        return resp, json.loads(body)


class TestCase(test.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()

        # If no credentials are provided, the Manager will use those
        # in CONF.identity and generate an auth_provider from them
        mgr = clients.Manager()
        cls.client = MuranoClient(mgr.auth_provider)

    def setUp(self):
        super(TestCase, self).setUp()

        self.environments = []

    def tearDown(self):
        super(TestCase, self).tearDown()

        for environment in self.environments:
            try:
                self.client.delete_environment(environment['id'])
            except exceptions.NotFound:
                pass

    def create_environment(self, name):
        environment = self.client.create_environment(name)[1]
        self.environments.append(environment)

        return environment

    def create_demo_service(self, environment_id, session_id, client=None):
        if not client:
            client = self.client
        post_body = {
            "?": {
                "id": uuid.uuid4().hex,
                "type": "io.murano.tests.demoService"
            },
            "availabilityZone": "nova",
            "name": "demo",
            "unitNamingPattern": "host",
            "osImage": {
                "type": "cirros.demo",
                "name": "demo",
                "title": "Demo"
            },
            "units": [{}],
            "flavor": "m1.small",
            "configuration": "standalone"
        }

        return client.create_service(environment_id,
                                     session_id,
                                     post_body)


class NegativeTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(NegativeTestCase, cls).setUpClass()

        # If no credentials are provided, the Manager will use those
        # in CONF.identity and generate an auth_provider from them
        creds = isolated_creds.IsolatedCreds(cls.__name__).get_alt_creds()
        mgr = clients.Manager(credentials=creds)
        cls.alt_client = MuranoClient(mgr.auth_provider)
