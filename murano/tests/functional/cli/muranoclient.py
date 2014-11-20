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

from tempest_lib.cli import base  # noqa

from tempest import config

CONF = config.CONF


class ClientTestBase(base.ClientTestBase):

    def murano(self, action, flags='', params='', admin=True, fail_ok=False):
        """Executes murano command for the given action."""
        return self.clients.cmd_with_auth(
            'murano', action, flags, params, admin, fail_ok)

    def _get_clients(self):
        clients = base.CLIClient(
            CONF.identity.admin_username,
            CONF.identity.admin_password,
            CONF.identity.admin_tenant_name,
            CONF.identity.uri,
            CONF.cli.cli_dir
        )
        return clients

    def listing(self, command, params=""):
        return self.parser.listing(self.murano(command, params=params))

    def get_value(self, need_field, known_field, known_value, somelist):
        for element in somelist:
            if element[known_field] == known_value:
                return element[need_field]
