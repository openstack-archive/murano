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


from eventlet import semaphore
import heatclient.client as hclient
import muranoclient.v1.client as muranoclient
import neutronclient.v2_0.client as nclient

from murano.common import config
from murano.dsl import helpers
from murano.engine import auth_utils
from murano.engine import environment


class ClientManager(object):
    def __init__(self):
        self._trusts_keystone_client = None
        self._token_keystone_client = None
        self._cache = {}
        self._semaphore = semaphore.BoundedSemaphore()

    def _get_environment(self, context):
        if isinstance(context, environment.Environment):
            return context
        return helpers.get_environment(context)

    def _get_client(self, context, name, use_trusts, client_factory):
        if not config.CONF.engine.use_trusts:
            use_trusts = False

        keystone_client = None if name == 'keystone' else \
            self.get_keystone_client(context, use_trusts)

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
                    env = self._get_environment(context)
                    token = env.token
                client = client_factory(keystone_client, token)
                self._cache[(name, use_trusts)] = (client, token)
            return client
        finally:
            self._semaphore.release()

    def get_keystone_client(self, context, use_trusts=True):
        if not config.CONF.engine.use_trusts:
            use_trusts = False
        env = self._get_environment(context)
        factory = lambda _1, _2: auth_utils.get_client_for_trusts(env) \
            if use_trusts else auth_utils.get_client(env)

        return self._get_client(context, 'keystone', use_trusts, factory)

    def get_heat_client(self, context, use_trusts=True):
        if not config.CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            heat_settings = config.CONF.heat

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

            if not config.CONF.engine.use_trusts:
                kwargs.update({
                    'username': 'badusername',
                    'password': 'badpassword'
                })
            return hclient.Client('1', heat_url, **kwargs)

        return self._get_client(context, 'heat', use_trusts, factory)

    def get_neutron_client(self, context, use_trusts=True):
        if not config.CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            neutron_settings = config.CONF.neutron

            neutron_url = keystone_client.service_catalog.url_for(
                service_type='network',
                endpoint_type=neutron_settings.endpoint_type)

            return nclient.Client(
                endpoint_url=neutron_url,
                token=auth_token,
                ca_cert=neutron_settings.ca_cert or None,
                insecure=neutron_settings.insecure)

        return self._get_client(context, 'neutron', use_trusts, factory)

    def get_murano_client(self, context, use_trusts=True):
        if not config.CONF.engine.use_trusts:
            use_trusts = False

        def factory(keystone_client, auth_token):
            murano_settings = config.CONF.murano

            murano_url = \
                murano_settings.url or keystone_client.service_catalog.url_for(
                    service_type='application_catalog',
                    endpoint_type=murano_settings.endpoint_type)

            return muranoclient.Client(
                endpoint=murano_url,
                key_file=murano_settings.key_file or None,
                cacert=murano_settings.cacert or None,
                cert_file=murano_settings.cert_file or None,
                insecure=murano_settings.insecure,
                auth_url=keystone_client.auth_url,
                token=auth_token)

        return self._get_client(context, 'murano', use_trusts, factory)
