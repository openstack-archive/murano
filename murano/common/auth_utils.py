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


from keystoneclient.v3 import client as ks_client
from oslo.config import cfg
from oslo.utils import importutils


def get_client(token, tenant_id):
    settings = _get_keystone_settings()
    kwargs = {
        'token': token,
        'tenant_id': tenant_id,
        'auth_url': settings['auth_url']
    }
    kwargs.update(settings['ssl'])
    keystone = ks_client.Client(**kwargs)
    keystone.management_url = settings['auth_url']

    return keystone


def get_client_for_admin(project_name):
    return _admin_client(project_name=project_name)


def _admin_client(trust_id=None, project_name=None):
    settings = _get_keystone_settings()

    kwargs = {
        'project_name': project_name,
        'trust_id': trust_id
    }
    for key in ('username', 'password', 'auth_url'):
        kwargs[key] = settings[key]
    kwargs.update(settings['ssl'])

    client = ks_client.Client(**kwargs)

    # without resetting this attributes keystone client cannot re-authenticate
    client.project_id = None
    client.project_name = None

    client.management_url = settings['auth_url']

    return client


def get_client_for_trusts(trust_id):
    return _admin_client(trust_id)


def create_trust(token, tenant_id):
    client = get_client(token, tenant_id)

    settings = _get_keystone_settings()
    trustee_id = get_client_for_admin(
        settings['project_name']).user_id

    roles = [t['name'] for t in client.auth_ref['roles']]
    trust = client.trusts.create(trustor_user=client.user_id,
                                 trustee_user=trustee_id,
                                 impersonation=True,
                                 role_names=roles,
                                 project=tenant_id)

    return trust.id


def delete_trust(trust_id):
    keystone_client = get_client_for_trusts(trust_id)
    keystone_client.trusts.delete(trust_id)


def _get_keystone_settings():
    importutils.import_module('keystonemiddleware.auth_token')
    return {
        'auth_url': cfg.CONF.keystone_authtoken.auth_uri.replace('v2.0', 'v3'),
        'username': cfg.CONF.keystone_authtoken.admin_user,
        'password': cfg.CONF.keystone_authtoken.admin_password,
        'project_name': cfg.CONF.keystone_authtoken.admin_tenant_name,
        'ssl': {
            'cacert': cfg.CONF.keystone.ca_file,
            'insecure': cfg.CONF.keystone.insecure,
            'cert': cfg.CONF.keystone.cert_file,
            'key': cfg.CONF.keystone.key_file
        }
    }
