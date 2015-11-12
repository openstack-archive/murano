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
from tempest_lib.common import rest_client

CONF = config.CONF


class ApplicationCatalogClient(rest_client.RestClient):
    """Tempest REST client for Murano Application Catalog"""

    def __init__(self, auth_provider):
        super(ApplicationCatalogClient, self).__init__(
            auth_provider,
            CONF.application_catalog.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.application_catalog.endpoint_type)
        self.build_interval = CONF.service_broker.build_interval
        self.build_timeout = CONF.service_broker.build_timeout

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
