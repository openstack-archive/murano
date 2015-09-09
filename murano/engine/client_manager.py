# Copyright (c) 2014 Mirantis, Inc.
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

import weakref

from eventlet import semaphore
import heatclient.client as hclient
import keystoneclient
import keystoneclient.auth.identity.access as access
import muranoclient.v1.client as muranoclient
import neutronclient.v2_0.client as nclient
from oslo_config import cfg

from murano.common import auth_utils
from muranoclient.glance import client as art_client

try:
    # integration with congress is optional
    import congressclient.v1.client as congress_client
except ImportError as congress_client_import_error:
    congress_client = None
try:
    import mistralclient.api.client as mistralclient
except ImportError as mistral_import_error:
    mistralclient = None

CONF = cfg.CONF


class ClientManager(object):
    def __init__(self, environment):
        self._trusts_keystone_client = None
        self._token_keystone_client = None
        self._cache = {}
        self._semaphore = semaphore.BoundedSemaphore()
        self._environment = weakref.proxy(environment)

    def get_client(self, name, use_trusts, client_factory):
        if not CONF.engine.use_trusts:
            use_trusts = False

        keystone_client = None if name == 'keystone' else \
            self.get_keystone_client(use_trusts)

        self._semaphore.acquire()
        try:
            client, used_token = self._cache.get(
                (name, use_trusts), (None, None))
            fresh_token = None if keystone_client is None \
                else keystone_client.auth_token
            if use_trusts and used_token != fresh_token:
                client = None
            if not client:
                token = fresh_token
                if not use_trusts:
                    token = self._environment.token
                client = client_factory(keystone_client, token)
                self._cache[(name, use_trusts)] = (client, token)
            return client
        finally:
            self._semaphore.release()

    def get_keystone_client(self, use_trusts=True):
        if not CONF.engine.use_trusts:
            use_trusts = False
        factory = lambda _1, _2: \
            auth_utils.get_client_for_trusts(self._environment.trust_id) \
            if use_trusts else auth_utils.get_client(
                self._environment.token, self._environment.tenant_id)

        return self.get_client('keystone', use_trusts, factory)

    def get_congress_client(self, use_trusts=True):
        """Client for congress services

        :return: initialized congress client
        :raise ImportError: in case that python-congressclient
        is not present on python path
        """

        if not congress_client:
            # congress client was not imported
            raise congress_client_import_error
        if not CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            auth = access.AccessInfoPlugin(keystone_client.auth_ref)
            session = keystoneclient.session.Session(auth=auth)
            return congress_client.Client(session=session,
                                          service_type='policy')

        return self.get_client('congress', use_trusts, factory)

    def get_heat_client(self, use_trusts=True):
        if not CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            heat_settings = CONF.heat

            heat_url = keystone_client.service_catalog.url_for(
                service_type='orchestration',
                endpoint_type=heat_settings.endpoint_type)

            kwargs = {
                'token': auth_token,
                'ca_file': heat_settings.ca_file or None,
                'cert_file': heat_settings.cert_file or None,
                'key_file': heat_settings.key_file or None,
                'insecure': heat_settings.insecure
            }

            if not CONF.engine.use_trusts:
                kwargs.update({
                    'username': 'badusername',
                    'password': 'badpassword'
                })
            return hclient.Client('1', heat_url, **kwargs)

        return self.get_client('heat', use_trusts, factory)

    def get_neutron_client(self, use_trusts=True):
        if not CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            neutron_settings = CONF.neutron

            neutron_url = keystone_client.service_catalog.url_for(
                service_type='network',
                endpoint_type=neutron_settings.endpoint_type)

            return nclient.Client(
                endpoint_url=neutron_url,
                token=auth_token,
                ca_cert=neutron_settings.ca_cert or None,
                insecure=neutron_settings.insecure)

        return self.get_client('neutron', use_trusts, factory)

    def get_murano_client(self, use_trusts=True):
        if not CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            murano_settings = CONF.murano

            murano_url = \
                murano_settings.url or keystone_client.service_catalog.url_for(
                    service_type='application_catalog',
                    endpoint_type=murano_settings.endpoint_type)

            if CONF.packages_opts.packages_service == 'glance':
                glance_settings = CONF.glance
                glance_url = (glance_settings.url or
                              keystone_client.service_catalog.url_for(
                                  service_type='image',
                                  endpoint_type=glance_settings.endpoint_type))

                arts = art_client.Client(
                    endpoint=glance_url, token=auth_token,
                    insecure=glance_settings.insecure,
                    key_file=glance_settings.key_file or None,
                    ca_file=glance_settings.ca_file or None,
                    cert_file=glance_settings.cert_file or None,
                    type_name='murano',
                    type_version=1)
            else:
                arts = None

            return muranoclient.Client(
                endpoint=murano_url,
                key_file=murano_settings.key_file or None,
                ca_file=murano_settings.cacert or None,
                cert_file=murano_settings.cert_file or None,
                insecure=murano_settings.insecure,
                auth_url=keystone_client.auth_url,
                token=auth_token,
                artifacts_client=arts)

        return self.get_client('murano', use_trusts, factory)

    def get_mistral_client(self, use_trusts=True):
        if not mistralclient:
            raise mistral_import_error

        if not CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            mistral_settings = CONF.mistral

            endpoint_type = mistral_settings.endpoint_type
            service_type = mistral_settings.service_type

            mistral_url = keystone_client.service_catalog.url_for(
                service_type=service_type,
                endpoint_type=endpoint_type)

            return mistralclient.client(mistral_url=mistral_url,
                                        project_id=keystone_client.tenant_id,
                                        endpoint_type=endpoint_type,
                                        service_type=service_type,
                                        auth_token=auth_token,
                                        user_id=keystone_client.user_id)

        return self.get_client('mistral', use_trusts, factory)

    def get_artifacts_client(self, use_trusts=True):
        if not CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            glance_settings = CONF.glance

            glance_url = (glance_settings.url or
                          keystone_client.service_catalog.url_for(
                              service_type='image',
                              endpoint_type=glance_settings.endpoint_type))

            return art_client.Client(endpoint=glance_url, token=auth_token,
                                     insecure=glance_settings.insecure,
                                     key_file=glance_settings.key_file or None,
                                     cacert=glance_settings.cacert or None,
                                     cert_file=(glance_settings.cert_file or
                                                None),
                                     type_name='murano',
                                     type_version=1)
        return self.get_client('artifacts', use_trusts, factory)
