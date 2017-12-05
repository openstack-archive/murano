# Copyright (c) 2015 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import congressclient.v1.client as cclient
from keystoneauth1 import identity
from keystoneauth1 import session as ksasession
import keystoneclient.v3 as ksclient
from tempest import config

import murano.tests.functional.common.utils as common_utils

CONF = config.CONF


class TempestDeployTestMixin(common_utils.DeployTestMixin):
    """Overrides methods to use tempest configuration."""

    @staticmethod
    @common_utils.memoize
    def keystone_client():
        return ksclient.Client(username=CONF.auth.admin_username,
                               password=CONF.auth.admin_password,
                               tenant_name=CONF.auth.admin_project_name,
                               auth_url=CONF.identity.uri_v3)

    @staticmethod
    @common_utils.memoize
    def congress_client():
        auth = identity.v3.Password(
            auth_url=CONF.identity.uri_v3,
            username=CONF.auth.admin_username,
            password=CONF.auth.admin_password,
            project_name=CONF.auth.admin_project_name,
            user_domain_name=CONF.auth.admin_domain_name,
            project_domain_name=CONF.auth.admin_domain_name)
        session = ksasession.Session(auth=auth)
        return cclient.Client(session=session,
                              service_type='policy')
