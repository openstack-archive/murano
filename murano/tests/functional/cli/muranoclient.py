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

import os

from tempest_lib.cli import base  # noqa


class ClientTestBase(base.ClientTestBase):

    def murano(self, action, flags='', params='',
               fail_ok=False, endpoint_type='publicURL', merge_stderr=True):
        return self.clients.cmd_with_auth(
            'murano', action, flags, params, fail_ok, merge_stderr)

    def _get_clients(self):
        clients = base.CLIClient(
            username=os.environ.get('OS_USERNAME'),
            password=os.environ.get('OS_PASSWORD'),
            tenant_name=os.environ.get('OS_TENANT_NAME'),
            uri=os.environ.get('OS_AUTH_URL'),
            # FIXME: see how it's done in saharaclient
            cli_dir='/usr/local/bin'
        )
        return clients

    def listing(self, command, params=""):
        return self.parser.listing(self.murano(command, params=params))

    def get_value(self, need_field, known_field, known_value, somelist):
        for element in somelist:
            if element[known_field] == known_value:
                return element[need_field]
