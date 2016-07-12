# Copyright (c) 2015 Mirantis, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import os

import requests
from tempest import config
from tempest.lib.common import rest_client

from murano_tempest_tests import utils

CONF = config.CONF


class ApplicationCatalogClient(rest_client.RestClient):
    """Tempest REST client for Murano Application Catalog"""

    def __init__(self, auth_provider):
        super(ApplicationCatalogClient, self).__init__(
            auth_provider,
            CONF.application_catalog.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.application_catalog.endpoint_type)
        self.build_interval = CONF.application_catalog.build_interval
        self.build_timeout = CONF.application_catalog.build_timeout

# -----------------------------Packages methods--------------------------------
    def upload_package(self, package_name, package_path, top_dir, body):
        """Upload a Murano package into Murano repository

        :param package_name: Package name
        :param package_path: Path with .zip relatively top_dir
        :param top_dir: Top directory with tests
        :param body: dict of tags, parameters, etc
        :return:
        """
        headers = {'X-Auth-Token': self.auth_provider.get_token()}
        files = open(os.path.join(top_dir, package_path), 'rb')
        uri = "/v1/catalog/packages"
        post_body = {'JsonString': json.dumps(body)}
        endpoint = self.base_url
        url = endpoint + uri
        resp = requests.post(url, files={package_name: files}, data=post_body,
                             headers=headers)
        self.expected_success(200, resp.status_code)
        return self._parse_resp(resp.text)

    def update_package(self, package_id, post_body):
        headers = {
            'content-type': 'application/murano-packages-json-patch'
        }

        uri = 'v1/catalog/packages/{0}'.format(package_id)
        resp, body = self.patch(uri, json.dumps(post_body), headers=headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_package(self, package_id):
        """Removes a package from a repository

        :param package_id: Package ID
        """
        uri = 'v1/catalog/packages/{0}'.format(package_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)

    def get_package(self, package_id):
        uri = 'v1/catalog/packages/{0}'.format(package_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_list_packages(self):
        uri = 'v1/catalog/packages'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def download_package(self, package_id):
        headers = {
            'content-type': 'application/octet-stream'
        }
        uri = 'v1/catalog/packages/{0}/download'.format(package_id)
        resp, body = self.get(uri, headers=headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_ui_definition(self, package_id):
        headers = {
            'content-type': 'application/octet-stream'
        }
        uri = 'v1/catalog/packages/{0}/ui'.format(package_id)
        resp, body = self.get(uri, headers=headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_logo(self, package_id):
        headers = {
            'content-type': 'application/octet-stream'
        }
        uri = 'v1/catalog/packages/{0}/ui'.format(package_id)
        resp, body = self.get(uri, headers=headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

# -----------------------Methods for environment CRUD--------------------------
    def get_environments_list(self):
        uri = 'v1/environments'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)

        return self._parse_resp(body)

    def create_environment(self, name):
        uri = 'v1/environments'
        post_body = {'name': name}
        resp, body = self.post(uri, json.dumps(post_body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_environment(self, environment_id):
        uri = 'v1/environments/{0}'.format(environment_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)

    def abandon_environment(self, environment_id):
        uri = 'v1/environments/{0}?abandon=True'.format(environment_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)

    def update_environment(self, environment_id):
        uri = 'v1/environments/{0}'.format(environment_id)
        name = utils.generate_name("updated_env")
        post_body = {"name": name}
        resp, body = self.put(uri, json.dumps(post_body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_environment(self, environment_id):
        uri = 'v1/environments/{0}'.format(environment_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

# -----------------------Methods for session manage ---------------------------
    def create_session(self, environment_id):
        body = None
        uri = 'v1/environments/{0}/configure'.format(environment_id)
        resp, body = self.post(uri, body)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_session(self, environment_id, session_id):
        uri = 'v1/environments/{0}/sessions/{1}'.format(environment_id,
                                                        session_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_session(self, environment_id, session_id):
        uri = 'v1/environments/{0}/sessions/{1}'.format(environment_id,
                                                        session_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def deploy_session(self, environment_id, session_id):
        body = None
        url = 'v1/environments/{0}/sessions/{1}/deploy'.format(environment_id,
                                                               session_id)
        resp, body = self.post(url, body)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

# -----------------------------Service methods---------------------------------
    def create_service(self, environment_id, session_id, post_body):
        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )
        uri = 'v1/environments/{0}/services'.format(environment_id)
        resp, body = self.post(uri, json.dumps(post_body), headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_service(self, environment_id, session_id, service_id):
        headers = self.get_headers()
        headers.update(
            {'X-Configuration-Session': session_id}
        )
        uri = 'v1/environments/{0}/services/{1}'.format(environment_id,
                                                        service_id)
        resp, body = self.delete(uri, headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_services_list(self, environment_id, session_id=None):
        headers = self.get_headers()
        if session_id:
            headers.update(
                {'X-Configuration-Session': session_id}
            )
        uri = 'v1/environments/{0}/services'.format(environment_id)
        resp, body = self.get(uri, headers)
        self.expected_success(200, resp.status)
        # TODO(freerunner): Need to replace json.loads() to _parse_resp
        # method, when fix for https://bugs.launchpad.net/tempest/+bug/1539927
        # will resolved and new version of tempest-lib released.
        return json.loads(body)

    def get_service(self, environment_id, service_id, session_id=None):
        headers = self.get_headers()
        if session_id:
            headers.update(
                {'X-Configuration-Session': session_id}
            )
        uri = 'v1/environments/{0}/services/{1}'.format(environment_id,
                                                        service_id)
        resp, body = self.get(uri, headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

# -----------------------------Category methods--------------------------------
    def list_categories(self):
        uri = 'v1/catalog/packages/categories'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def create_category(self, name):
        body = {'name': name}
        uri = 'v1/catalog/categories'
        resp, body = self.post(uri, json.dumps(body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_category(self, category_id):
        uri = 'v1/catalog/categories/{0}'.format(category_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_category(self, category_id):
        uri = 'v1/catalog/categories/{0}'.format(category_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

# ----------------------Environment templates methods--------------------------
    def get_env_templates_list(self):
        uri = 'v1/templates'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_public_env_templates_list(self):
        uri = 'v1/templates?is_public=true'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_private_env_templates_list(self):
        uri = 'v1/templates?is_public=false'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def create_env_template(self, env_template_name):
        body = {'name': env_template_name, "is_public": False,
                "description_text": "description"}
        uri = 'v1/templates'
        resp, body = self.post(uri, json.dumps(body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def clone_env_template(self, env_template_id, cloned_env_template_name):
        body = {'name': cloned_env_template_name}
        uri = 'v1/templates/{0}/clone'.format(env_template_id)
        resp, body = self.post(uri, json.dumps(body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def create_public_env_template(self, env_template_name):
        body = {'name': env_template_name, "is_public": True}
        uri = 'v1/templates'
        resp, body = self.post(uri, json.dumps(body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def create_env_template_with_services(self, env_template_name, post_body):
        body = {
            'name': env_template_name,
            'services': [post_body]
        }
        uri = 'v1/templates'
        resp, body = self.post(uri, json.dumps(body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def create_service_in_env_template(self, env_template_id, post_body):
        uri = 'v1/templates/{0}/services'.format(env_template_id)
        resp, body = self.post(uri, json.dumps(post_body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_services_list_in_env_template(self, env_template_id):
        uri = 'v1/templates/{0}/services'.format(env_template_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        # TODO(freerunner): Need to replace json.loads() to _parse_resp
        # method, when fix for https://bugs.launchpad.net/tempest/+bug/1539927
        # will resolved and new version of tempest-lib released.
        return json.loads(body)

    def get_service_in_env_template(self, env_template_name, service_id):
        uri = 'v1/templates/{0}/services/{1}'.format(env_template_name,
                                                     service_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return json.loads(body)

    def update_service_from_env_template(self, env_template_id, service_id,
                                         post_body):
        uri = 'v1/templates/{0}/services/{1}'.format(env_template_id,
                                                     service_id)
        resp, body = self.put(uri, json.dumps(post_body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_service_from_env_template(self, env_template_name, service_id):
        uri = 'v1/templates/{0}/services/{1}'.format(env_template_name,
                                                     service_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_env_template(self, env_template_id):
        uri = 'v1/templates/{0}'.format(env_template_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_env_template(self, env_template_id):
        uri = 'v1/templates/{0}'.format(env_template_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def create_env_from_template(self, env_template_id, env_name):
        body = {'name': env_name}
        uri = 'v1/templates/{0}/create-environment'.format(env_template_id)
        resp, body = self.post(uri, json.dumps(body))
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

# ----------------------------Static action methods----------------------------
    def call_static_action(self, class_name=None, method_name=None, args=None,
                           package_name=None, class_version="=0"):
        uri = 'v1/actions'
        post_body = {
            'parameters': args or {},
            'packageName': package_name,
            'classVersion': class_version
        }
        if class_name:
            post_body['className'] = class_name
        if method_name:
            post_body['methodName'] = method_name

        resp, body = self.post(uri, json.dumps(post_body))
        self.expected_success(200, resp.status)
        # _parse_resp() cannot be used because body is expected to be string
        return body
