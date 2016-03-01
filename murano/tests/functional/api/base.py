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
from tempest.common import credentials_factory as common_creds
from tempest.common import dynamic_creds
from tempest import config
from tempest.lib.common import rest_client
from tempest.lib import exceptions
from tempest import test


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
        body = {'name': name}
        resp, body = self.post('v1/environments', json.dumps(body))

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

        return resp

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
        if session_id:
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

    def get_env_templates_list(self):
        """Check the environment templates deployed by the user."""
        resp, body = self.get('v1/templates')

        return resp, json.loads(body)

    def create_env_template(self, env_template_name):
        """Check the creation of an environment template."""
        body = {'name': env_template_name}
        resp, body = self.post('v1/templates', json.dumps(body))

        return resp, json.loads(body)

    def create_env_template_with_apps(self, env_template_name):
        """Check the creation of an environment template."""
        body = {'name': env_template_name}
        body['services'] = [self._get_demo_app()]
        resp, body = self.post('v1/templates', json.dumps(body))
        return resp, json.loads(body)

    def create_app_in_env_template(self, env_template_name):
        """Check the creation of an environment template."""
        resp, body = self.post('v1/templates/{0}/services'.
                               format(env_template_name),
                               json.dumps(self._get_demo_app()))
        return resp, json.loads(body)

    def get_apps_in_env_template(self, env_template_name):
        """Check getting information about applications
        in an environment template.
        """
        resp, body = self.get('v1/templates/{0}/services'.
                              format(env_template_name))
        return resp, json.loads(body)

    def get_app_in_env_template(self, env_template_name, app_name):
        """Check getting information about an application
        in an environment template.
        """
        resp, body = self.get('v1/templates/{0}/services/{1}'.
                              format(env_template_name, app_name))
        return resp, json.loads(body)

    def delete_app_in_env_template(self, env_template_name):
        """Delete an application in an environment template."""
        resp, body = self.delete('v1/templates/{0}/services/{1}'.
                                 format(env_template_name, 'ID'))
        return resp

    def delete_env_template(self, env_template_id):
        """Check the deletion of an environment template."""
        resp, body = self.delete('v1/templates/{0}'.format(env_template_id))
        return resp

    def get_env_template(self, env_template_id):
        """Check getting information of an environment template."""
        resp, body = self.get('v1/templates/{0}'.format(env_template_id))

        return resp, json.loads(body)

    def create_env_from_template(self, env_template_id, env_name):
        """Check creating an environment from a template."""
        body = {'name': env_name}
        resp, body = self.post('v1/templates/{0}/create-environment'.
                               format(env_template_id),
                               json.dumps(body))
        return resp, json.loads(body)

    def _get_demo_app(self):
        return {
            "instance": {
                "assignFloatingIp": "true",
                "keyname": "mykeyname",
                "image": "cloud-fedora-v3",
                "flavor": "m1.medium",
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                }
            },
            "name": "orion",
            "port": "8080",
            "?": {
                "type": "io.murano.apps.apache.Tomcat",
                "id": "ID"
            }
        }


class TestCase(test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()

        # If no credentials are provided, the Manager will use those
        # in CONF.identity and generate an auth_provider from them
        cls.creds = common_creds.get_configured_credentials(
            credential_type='identity_admin')
        mgr = clients.Manager(cls.creds)
        cls.client = MuranoClient(mgr.auth_provider)

    def setUp(self):
        super(TestCase, self).setUp()

        self.environments = []
        self.env_templates = []

    def tearDown(self):
        super(TestCase, self).tearDown()

        for environment in self.environments:
            try:
                self.client.delete_environment(environment['id'])
            except exceptions.NotFound:
                pass

        for env_template in self.env_templates:
            try:
                self.client.delete_env_template(env_template['id'])
            except exceptions.NotFound:
                pass

    def create_environment(self, name):
        environment = self.client.create_environment(name)[1]
        self.environments.append(environment)

        return environment

    def create_env_template(self, name):
        env_template = self.client.create_env_template(name)[1]
        self.env_templates.append(env_template)

        return env_template

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
        admin_creds = common_creds.get_configured_credentials(
            credential_type='identity_admin')

        cls.dynamic_creds = dynamic_creds.DynamicCredentialProvider(
            identity_version='v2', name=cls.__name__, admin_creds=admin_creds)
        creds = cls.dynamic_creds.get_alt_creds()
        mgr = clients.Manager(credentials=creds)
        cls.alt_client = MuranoClient(mgr.auth_provider)

    @classmethod
    def purge_creds(cls):
        cls.dynamic_creds.clear_creds()
