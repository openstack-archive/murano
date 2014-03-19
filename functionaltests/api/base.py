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

from tempest import clients
from tempest.common import rest_client
from tempest import config
import testtools

CONF = config.CONF


class MuranoClient(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(MuranoClient, self).__init__(auth_provider)
        self.service = 'application_catalog'
        self.endpoint_url = 'publicURL'


class TestCase(testtools.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        username = CONF.identity.username
        password = CONF.identity.password
        tenant_name = CONF.identity.tenant_name
        mgr = clients.Manager(username, password, tenant_name)
        auth_provider = mgr.get_auth_provider()
        self.client = MuranoClient(auth_provider)
