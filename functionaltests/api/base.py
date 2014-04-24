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
import testtools
import uuid

from tempest import clients
from tempest.common import rest_client
from tempest import config
from tempest import exceptions

CONF = config.CONF


class MuranoClient(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(MuranoClient, self).__init__(auth_provider)

        self.service = 'application_catalog'
        self.endpoint_url = 'publicURL'

    def get_environments_list(self):
        resp, body = self.get('environments')

        return resp, json.loads(body)

    def create_environment(self, name):
        post_body = '{"name": "%s"}' % name

        resp, body = self.post('environments', post_body)

        return resp, json.loads(body)

    def delete_environment(self, environment_id):
        return self.delete('environments/{0}'.format(environment_id))

    def update_environment(self, environment_id):
        post_body = '{"name": "%s"}' % ("changed-environment-name")

        resp, body = self.put('environments/{0}'.format(environment_id),
                              post_body)

        return resp, json.loads(body)

    def get_environment(self, environment_id):
        resp, body = self.get('environments/{0}'.format(environment_id))

        return resp, json.loads(body)

    def create_session(self, environment_id):
        post_body = None

        resp, body = self.post(
            'environments/{0}/configure'.format(environment_id),
            post_body
        )

        return resp, json.loads(body)

    def delete_session(self, environment_id, session_id):
        return self.delete(
            'environments/{0}/sessions/{1}'.format(environment_id, session_id))

    def get_session(self, environment_id, session_id):
        resp, body = self.get(
            'environments/{0}/sessions/{1}'.format(environment_id, session_id))

        return resp, json.loads(body)

    def create_service(self, environment_id, session_id, post_body):
        post_body = json.dumps(post_body)

        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )

        resp, body = self.post(
            'environments/{0}/services'.format(environment_id),
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
            'environments/{0}/services/{1}'.format(environment_id, service_id),
            headers
        )

    def get_services_list(self, environment_id, session_id):
        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )

        resp, body = self.get(
            'environments/{0}/services'.format(environment_id),
            headers
        )

        return resp, json.loads(body)

    def get_service(self, environment_id, session_id, service_id):
        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )

        resp, body = self.get(
            'environments/{0}/services/{1}'.format(environment_id, service_id),
            headers
        )

        return resp, json.loads(body)

    def get_list_packages(self):
        resp, body = self.get('catalog/packages')

        return resp, json.loads(body)

    def get_package(self, id):
        resp, body = self.get('catalog/packages/{0}'.format(id))

        return resp, json.loads(body)

    def upload_package(self, package_name, body):
        __location__ = os.path.realpath(os.path.join(
            os.getcwd(), os.path.dirname(__file__)))

        headers = {'X-Auth-Token': self.auth_provider.get_token()}

        files = {'%s' % package_name: open(
            os.path.join(__location__, 'v1/DummyTestApp.zip'), 'rb')}

        post_body = {'JsonString': json.dumps(body)}
        request_url = '{endpoint}{url}'.format(endpoint=self.base_url,
                                               url='/catalog/packages')

        resp = requests.post(request_url, files=files, data=post_body,
                             headers=headers)

        return resp

    def update_package(self, id, post_body):
        headers = {
            'X-Auth-Token': self.auth_provider.get_token(),
            'content-type': 'application/murano-packages-json-patch'
        }

        resp, body = self.patch('catalog/packages/{0}'.format(id),
                                json.dumps(post_body), headers=headers)

        return resp, json.loads(body)

    def delete_package(self, id):
        return self.delete('catalog/packages/{0}'.format(id))

    def download_package(self, id):
        return self.get('catalog/packages/{0}/download'.format(id))

    def get_ui_definition(self, id):
        return self.get('catalog/packages/{0}/ui'.format(id))

    def get_logo(self, id):
        return self.get('catalog/packages/{0}/logo'.format(id))

    def list_categories(self):
        resp, body = self.get('catalog/packages/categories')

        return resp, json.loads(body)


class TestCase(testtools.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()

        username = CONF.identity.username
        password = CONF.identity.password
        tenant_name = CONF.identity.tenant_name

        mgr = clients.Manager(username, password, tenant_name)
        auth_provider = mgr.get_auth_provider(mgr.get_default_credentials())

        cls.client = MuranoClient(auth_provider)

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

    def create_demo_service(self, environment_id, session_id):
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

        return self.client.create_service(environment_id,
                                          session_id,
                                          post_body)


class NegativeTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(NegativeTestCase, cls).setUpClass()

        username = CONF.identity.alt_username
        password = CONF.identity.alt_password
        tenant_name = CONF.identity.alt_tenant_name

        mgr = clients.Manager(username, password, tenant_name)
        auth_provider = mgr.get_auth_provider(mgr.get_default_credentials())

        cls.alt_client = MuranoClient(auth_provider)
