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
from tempest.common import dynamic_creds
from tempest import config
from tempest import test

from murano_tempest_tests import clients

CONF = config.CONF


class BaseApplicationCatalogTest(test.BaseTestCase):
    """Base test class for Murano Service Broker API tests."""

    @classmethod
    def get_client_with_isolated_creds(cls, type_of_creds="admin"):

        creds = cls.get_configured_isolated_creds(type_of_creds=type_of_creds)

        os = clients.Manager(credentials=creds)
        client = os.application_catalog_client

        return client

    @classmethod
    def get_configured_isolated_creds(cls, type_of_creds='admin'):

        identity_version = cls.get_identity_version()
        if identity_version == 'v3':
            cls.admin_role = CONF.identity.admin_role
        else:
            cls.admin_role = 'admin'
        cls.dynamic_cred = dynamic_creds.DynamicCredentialProvider(
            identity_version=CONF.application_catalog.identity_version,
            name=cls.__name__, admin_role=cls.admin_role,
            admin_creds=common_creds.get_configured_credentials(
                'identity_admin'))
        if type_of_creds == 'primary':
            creds = cls.dynamic_cred.get_primary_creds()
        elif type_of_creds == 'admin':
            creds = cls.dynamic_cred.get_admin_creds()
        elif type_of_creds == 'alt':
            creds = cls.dynamic_cred.get_alt_creds()
        else:
            creds = cls.dynamic_cred.get_credentials(type_of_creds)
        cls.dynamic_cred.type_of_creds = type_of_creds

        return creds

    @classmethod
    def verify_nonempty(cls, *args):
        if not all(args):
            msg = "Missing API credentials in configuration."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        if not CONF.service_available.murano:
            skip_msg = "Murano is disabled"
            raise cls.skipException(skip_msg)
        super(BaseApplicationCatalogTest, cls).resource_setup()
        if not hasattr(cls, "os"):
            creds = cls.get_configured_isolated_creds(type_of_creds='primary')
            cls.os = clients.Manager(credentials=creds)
        cls.application_catalog_client = cls.os.application_catalog_client

    def setUp(self):
        super(BaseApplicationCatalogTest, self).setUp()
        self.addCleanup(self.clear_isolated_creds)

    @classmethod
    def resource_cleanup(cls):
        super(BaseApplicationCatalogTest, cls).resource_cleanup()
        cls.clear_isolated_creds()

    @classmethod
    def clear_isolated_creds(cls):
        if hasattr(cls, "dynamic_cred"):
            cls.dynamic_cred.clear_creds()


class BaseApplicationCatalogAdminTest(BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        cls.os = clients.Manager()
        super(BaseApplicationCatalogAdminTest, cls).resource_setup()


class BaseApplicationCatalogIsolatedAdminTest(BaseApplicationCatalogTest):

    @classmethod
    def resource_setup(cls):
        creds = cls.get_configured_isolated_creds(type_of_creds='admin')
        cls.os = clients.Manager(credentials=creds)
        super(BaseApplicationCatalogIsolatedAdminTest, cls).resource_setup()
