# Copyright (c) 2016 Mirantis, Inc.
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


from keystoneclient.auth import identity
from keystoneclient import session as ks_session
from keystoneclient.v3 import client as ks_client
from oslo_config import cfg
from oslo_utils import importutils

from murano.dsl import helpers


@helpers.memoize
def _get_keystone_admin_parameters(scoped):
    importutils.import_module('keystonemiddleware.auth_token')
    settings = {
        'auth_url': cfg.CONF.keystone_authtoken.auth_uri.replace('v2.0', 'v3'),
        'username': cfg.CONF.keystone_authtoken.admin_user,
        'password': cfg.CONF.keystone_authtoken.admin_password,
        'user_domain_name': 'default'
    }
    if scoped:
        settings.update({
            'project_name': cfg.CONF.keystone_authtoken.admin_tenant_name,
            'project_domain_name': 'default'
        })
    return settings


@helpers.memoize
def create_keystone_admin_client(scoped):
    kwargs = _get_keystone_admin_parameters(scoped)
    password_auth = identity.Password(**kwargs)
    session = ks_session.Session(auth=password_auth)
    _set_ssl_parameters(cfg.CONF.keystone_authtoken, session)
    return ks_client.Client(session=session)


def get_client_session(execution_session=None, conf=None):
    if not execution_session:
        execution_session = helpers.get_execution_session()
    trust_id = execution_session.trust_id
    if trust_id is None:
        return get_token_client_session(
            token=execution_session.token,
            project_id=execution_session.project_id)
    kwargs = _get_keystone_admin_parameters(False)
    kwargs['trust_id'] = trust_id
    password_auth = identity.Password(**kwargs)
    session = ks_session.Session(auth=password_auth)
    _set_ssl_parameters(conf, session)
    return session


def get_token_client_session(token=None, project_id=None, conf=None):
    auth_url = _get_keystone_admin_parameters(False)['auth_url']
    if token is None or project_id is None:
        execution_session = helpers.get_execution_session()
        token = execution_session.token
        project_id = execution_session.project_id
    token_auth = identity.Token(auth_url, token=token, project_id=project_id)
    session = ks_session.Session(auth=token_auth)
    _set_ssl_parameters(conf, session)
    return session


def create_keystone_client(token=None, project_id=None, conf=None):
    return ks_client.Client(session=get_token_client_session(
        token=token, project_id=project_id, conf=conf))


def create_trust(trustee_token=None, trustee_project_id=None):
    admin_client = create_keystone_admin_client(True)
    user_client = create_keystone_client(
        token=trustee_token, project_id=trustee_project_id)
    trustee_user = admin_client.session.auth.get_user_id(admin_client.session)
    auth_ref = user_client.session.auth.get_access(user_client.session)
    trustor_user = auth_ref.user_id
    project = auth_ref.project_id
    roles = auth_ref.role_names
    trust = user_client.trusts.create(
        trustor_user=trustor_user,
        trustee_user=trustee_user,
        impersonation=True,
        role_names=roles,
        project=project)
    return trust.id


def delete_trust(trust):
    user_client = create_keystone_admin_client(True)
    user_client.trusts.delete(trust)


def _get_config_option(conf_section, option_names, default=None):
    if not isinstance(option_names, (list, tuple)):
        option_names = (option_names,)
    for name in option_names:
        if hasattr(conf_section, name):
            return getattr(conf_section, name)
    return default


def _set_ssl_parameters(conf_section, session):
    if not conf_section:
        return
    insecure = _get_config_option(conf_section, 'insecure', False)
    if insecure:
        session.verify = False
    else:
        session.verify = _get_config_option(
            conf_section, ('ca_file', 'cafile', 'cacert')) or True

    cert_file = _get_config_option(conf_section, ('cert_file', 'certfile'))
    key_file = _get_config_option(conf_section, ('key_file', 'keyfile'))

    if cert_file and key_file:
        session.cert = (cert_file, key_file)
    elif cert_file:
        session.cert = cert_file
    else:
        session.cert = None


def get_session_client_parameters(service_type=None,
                                  region='',
                                  interface=None,
                                  service_name=None,
                                  conf=None,
                                  session=None,
                                  execution_session=None):
    if region == '':
        region = cfg.CONF.home_region
    result = {
        'session': session or get_client_session(
            execution_session=execution_session, conf=conf)
    }

    url = _get_config_option(conf, 'url')
    if url:
        result['endpoint_override'] = url
    else:
        if not interface:
            interface = _get_config_option(conf, 'endpoint_type')
        result.update({
            'service_type': service_type,
            'service_name': service_name,
            'interface': interface,
            'region_name': region
        })
    return result
