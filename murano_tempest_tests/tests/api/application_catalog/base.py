# Copyright (c) 2016 Mirantis, Inc.
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

from tempest.common import credentials_factory as common_creds
from tempest import config
from tempest import test

from murano_tempest_tests import clients
from murano_tempest_tests import utils

CONF = config.CONF


class BaseApplicationCatalogTest(test.BaseTestCase):
    """Base test class for Murano Service Broker API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseApplicationCatalogTest, cls).skip_checks()
        if not CONF.service_available.murano:
            skip_msg = "Murano is disabled"
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(BaseApplicationCatalogTest, cls).setup_clients()
        if not hasattr(cls, "os_primary"):
            creds = cls.get_configured_isolated_creds(type_of_creds='primary')
            cls.os_primary = clients.Manager(credentials=creds)
        cls.application_catalog_client = \
            cls.os_primary.application_catalog_client
        cls.artifacts_client = cls.os_primary.artifacts_client

    @classmethod
    def get_client_with_isolated_creds(cls, type_of_creds="admin"):
        creds = cls.get_configured_isolated_creds(type_of_creds=type_of_creds)

        os = clients.Manager(credentials=creds)
        client = os.application_catalog_client

        return client

    @classmethod
    def get_configured_isolated_creds(cls, type_of_creds='admin'):
        identity_version = CONF.identity.auth_version
        if identity_version == 'v3':
            cls.admin_role = CONF.identity.admin_role
        else:
            cls.admin_role = 'admin'
        cls.credentials = common_creds.get_credentials_provider(
            name=cls.__name__,
            force_tenant_isolation=CONF.auth.use_dynamic_credentials,
            identity_version=CONF.identity.auth_version)
        if type_of_creds == 'primary':
            creds = cls.credentials.get_primary_creds()
        elif type_of_creds == 'admin':
            creds = cls.credentials.get_admin_creds()
        elif type_of_creds == 'alt':
            creds = cls.credentials.get_alt_creds()
        else:
            creds = cls.credentials.get_credentials(type_of_creds)
        cls.credentials.type_of_creds = type_of_creds

        return creds.credentials

    @staticmethod
    def _get_demo_app():
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
                "id": utils.generate_uuid()
            }
        }


class BaseApplicationCatalogIsolatedAdminTest(BaseApplicationCatalogTest):

    @classmethod
    def setup_clients(cls):
        super(BaseApplicationCatalogIsolatedAdminTest, cls).setup_clients()
        if not hasattr(cls, "os_admin"):
            creds = cls.get_configured_isolated_creds(type_of_creds='admin')
            cls.os_admin = clients.Manager(credentials=creds)
        cls.application_catalog_client = \
            cls.os_admin.application_catalog_client
        cls.artifacts_client = cls.os_admin.artifacts_client
