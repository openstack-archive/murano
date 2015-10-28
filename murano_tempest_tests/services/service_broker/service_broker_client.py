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

from tempest import config
from tempest_lib.common import rest_client

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
        headers = {"Authorization": "Basic " + encoded_auth}
        return headers

    def get_applications_list(self):
        """Get list of all available applications"""
        uri = "/v2/catalog"
        resp, body = self.get(uri, headers=self.headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)
