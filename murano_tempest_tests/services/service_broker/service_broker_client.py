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

import base64
import json

from tempest import config
from tempest.lib.common import rest_client

from murano_tempest_tests import utils

CONF = config.CONF


class ServiceBrokerClient(rest_client.RestClient):
    """Tempest REST client for Murano Service Broker"""

    def __init__(self, auth_provider):
        super(ServiceBrokerClient, self).__init__(
            auth_provider,
            CONF.service_broker.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.service_broker.endpoint_type)
        self.build_interval = CONF.service_broker.build_interval
        self.build_timeout = CONF.service_broker.build_timeout
        self.headers = self._generate_headers(auth_provider)

    @classmethod
    def _generate_headers(cls, auth_provider):
        """Generate base64-encoded auth string for murano-cfapi

        :param auth_provider:
        :return: headers
        """
        uname = auth_provider.credentials.username
        pwd = auth_provider.credentials.password

        encoded_auth = base64.b64encode('{0}:{1}'.format(uname, pwd))
        headers = {"Authorization": "Basic " + encoded_auth,
                   'content-type': 'application/json'}
        return headers

    def get_applications_list(self):
        """Get list of all available applications"""
        uri = "/v2/catalog"
        resp, body = self.get(uri, headers=self.headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def provision(self, instance_id, service_id, plan_id, space_id, post_json):
        """Create new service resources for developer"""
        uri = '/v2/service_instances/{0}?accepts_incomplete=true'.\
            format(instance_id)
        body = {
            'service_id': service_id,
            'plan_id': plan_id,
            'organization_guid': self.tenant_id,
            'space_guid': space_id,
            'parameters': post_json
        }
        body = json.dumps(body)
        resp, body = self.put(uri, body, headers=self.headers)
        self.expected_success([200, 202], resp.status)
        return body

    def deprovision(self, instance_id):
        uri = '/v2/service_instances/{0}?accepts_incomplete=true'.\
            format(instance_id)
        resp, body = self.delete(uri, headers=self.headers)
        self.expected_success(202, resp.status)
        return body

    def get_last_status(self, instance_id):
        uri = '/v2/service_instances/{0}/last_operation'.format(instance_id)
        resp, body = self.get(uri, headers=self.headers)
        self.expected_success([200, 202], resp.status)
        return self._parse_resp(body)

    def get_application(self, name, app_list):
        for app in app_list:
            if app['name'] == name:
                return app

    def create_binding(self, instance_id):
        binding_id = utils.generate_uuid()
        uri = "/v2/service_instances/{0}/service_bindings/{1}".format(
            instance_id, binding_id)
        post_body = {
            "plan_id": utils.generate_uuid(),
            "service_id": utils.generate_uuid(),
            "app_guid": utils.generate_uuid()
        }
        body = json.dumps(post_body)
        resp, body = self.put(uri, body, headers=self.headers)
        self.expected_success([200, 201], resp.status)
        return self._parse_resp(body)
