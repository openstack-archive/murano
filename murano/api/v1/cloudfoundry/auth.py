#    Copyright (c) 2015 Mirantis, Inc.
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

from keystoneclient.v3 import client
from oslo_config import cfg

CONF = cfg.CONF


def authenticate(user, password, tenant=None):
    project_name = tenant or CONF.cfapi.tenant
    keystone = client.Client(username=user,
                             password=password,
                             project_name=project_name,
                             auth_url=CONF.cfapi.auth_url.replace(
                                 'v2.0', 'v3'))
    return keystone
