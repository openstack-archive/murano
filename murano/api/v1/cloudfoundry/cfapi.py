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

import base64
import json
import uuid

import muranoclient.client as muranoclient
from muranoclient.glance import client as glare_client
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import loopingcall
from webob import exc

from murano.api.v1.cloudfoundry import auth as keystone_auth
from murano.common.i18n import _LI, _LW
from murano.common import wsgi
from murano.db.services import cf_connections as db_cf


cfapi_opts = [
    cfg.StrOpt('tenant', default='admin',
               help=('Tenant for service broker')),
    cfg.StrOpt('bind_host', default='localhost',
               help=('host for service broker')),
    cfg.StrOpt('bind_port', default='8083',
               help=('host for service broker')),
    cfg.StrOpt('auth_url', default='localhost:5000/v2.0')]

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CONF.register_opts(cfapi_opts, group='cfapi')


class Controller(object):
    """WSGI controller for application catalog resource in Murano v1 API"""

    def _package_to_service(self, package):
        srv = {}
        srv['id'] = package.id
        srv['name'] = package.name
        srv['description'] = package.description
        srv['bindable'] = True
        srv['tags'] = []
        for tag in package.tags:
            srv['tags'].append(tag.name)
        plan = {'id': package.id + '-1',
                'name': 'default',
                'description': 'Default plan for the service {name}'.format(
                    name=package.name)}
        srv['plans'] = [plan]
        return srv

    def _check_auth(self, req, tenant=None):
        auth = req.headers.get('Authorization', None)
        if auth is None:
            raise exc.HTTPUnauthorized(explanation='Bad credentials')

        auth_info = auth.split(' ')[1]
        auth_decoded = base64.b64decode(auth_info)
        user = auth_decoded.split(':')[0]
        password = auth_decoded.split(':')[1]
        if tenant:
            keystone = keystone_auth.authenticate(user, password, tenant)
        else:
            keystone = keystone_auth.authenticate(user, password)
        return (user, password, keystone)

    def _make_service(self, name, package, plan_id):
        id = uuid.uuid4().hex

        return {"name": name,
                "?": {plan_id: {"name": package.name},
                      "type": package.fully_qualified_name,
                      "id": id}}

    def _get_service(self, env, service_id):
        for service in env.services:
            if service['?']['id'] == service_id:
                return service
        return None

    def list(self, req):
        user, _, keystone = self._check_auth(req)
        # Once we get here we were authorized by keystone
        token = keystone.auth_token

        m_cli = _get_muranoclient(token)
        kwargs = {'type': 'Application'}
        packages = m_cli.packages.filter(**kwargs)

        services = []
        for package in packages:
            services.append(self._package_to_service(package))

        resp = {'services': services}

        return resp

    def provision(self, req, body, instance_id):
        """Here is the example of request body given us from Cloud Foundry:

         {
         "service_id":        "service-guid-here",
         "plan_id":           "plan-guid-here",
         "organization_guid": "org-guid-here",
         "space_guid":        "space-guid-here",
         "parameters": {"param1": "value1",
                        "param2": "value2"}
         }
        """
        data = json.loads(req.body)
        space_guid = data['space_guid']
        org_guid = data['organization_guid']
        plan_id = data['plan_id']
        service_id = data['service_id']
        parameters = data['parameters']
        self.current_session = None

        # Here we'll take an entry for CF org and space from db. If we
        # don't have any entries we will create it from scratch.
        try:
            tenant = db_cf.get_tenant_for_org(org_guid)
        except AttributeError:
            # FIXME(Kezar): need to find better way to get tenant
            tenant = CONF.cfapi.tenant
            db_cf.set_tenant_for_org(org_guid, tenant)
            LOG.info(_LI("Cloud Foundry {org_id} mapped to tenant "
                         "{tenant_name}").format(org_id=org_guid,
                                                 tenant_name=tenant))

        # Now as we have all parameters we can try to auth user in actual
        # tenant

        user, _, keystone = self._check_auth(req, tenant)
        # Once we get here we were authorized by keystone
        token = keystone.auth_token
        m_cli = _get_muranoclient(token)
        try:
            environment_id = db_cf.get_environment_for_space(space_guid)
        except AttributeError:
            body = {'name': 'my_{uuid}'.format(uuid=uuid.uuid4().hex)}
            env = m_cli.environments.create(body)
            environment_id = env.id
            db_cf.set_environment_for_space(space_guid, environment_id)
            LOG.info(_LI("Cloud Foundry {space_id} mapped to {environment_id}")
                     .format(space_id=space_guid,
                             environment_id=environment_id))

        package = m_cli.packages.get(service_id)
        LOG.debug('Adding service {name}'.format(name=package.name))

        service = self._make_service(space_guid, package, plan_id)
        db_cf.set_instance_for_service(instance_id, service['?']['id'],
                                       environment_id, tenant)
        # NOTE(Kezar): Here we are going through JSON and add ids where
        # it's necessary
        params = [parameters]
        while params:
            a = params.pop()
            for k, v in a.iteritems():
                if isinstance(v, dict):
                    params.append(v)
                    if k == '?':
                        v['id'] = uuid.uuid4().hex
        service.update(parameters)
        # Now we need to obtain session to modify the env
        session_id = create_session(m_cli, environment_id)
        m_cli.services.post(environment_id,
                            path='/',
                            data=service,
                            session_id=session_id)
        m_cli.sessions.deploy(environment_id, session_id)
        self.current_session = session_id
        return {}

    def deprovision(self, req, instance_id):
        service = db_cf.get_service_for_instance(instance_id)
        if not service:
            return {}

        service_id = service.service_id
        environment_id = service.environment_id
        tenant = service.tenant
        _, _, keystone = self._check_auth(req, tenant)
        # Once we get here we were authorized by keystone
        token = keystone.auth_token
        m_cli = _get_muranoclient(token)

        try:
            session_id = create_session(m_cli, environment_id)
        except exc.HTTPForbidden:
            # FIXME(Kezar): this is a temporary solution, should be replaced
            # with 'incomplete' response for Cloud Foudry as soon as we will
            # know which is right format for it.
            LOG.warning(_LW("Can't create new session. Please remove service "
                            "manually in environment {0}")
                        .format(environment_id))
            return {}

        m_cli.services.delete(environment_id, '/' + service_id, session_id)
        m_cli.sessions.deploy(environment_id, session_id)
        return {}

    def bind(self, req, body, instance_id, app_id):
        db_service = db_cf.get_service_for_instance(instance_id)
        if not db_service:
            return {}

        service_id = db_service.service_id
        environment_id = db_service.environment_id
        tenant = db_service.tenant
        _, _, keystone = self._check_auth(req, tenant)
        # Once we get here we were authorized by keystone
        token = keystone.auth_token
        m_cli = _get_muranoclient(token)

        session_id = create_session(m_cli, environment_id)
        env = m_cli.environments.get(environment_id, session_id)
        LOG.debug('Got environment {0}'.format(env))
        service = self._get_service(env, service_id)
        LOG.debug('Got service {0}'.format(service))

        # NOTE(starodubcevna): Here we need to find an action which will return
        # us needed credentials. By default we will looking for getCredentials
        # action.
        result = {}
        try:
            actions = service['?']['_actions']
            for action_id in list(actions):
                if 'getCredentials' in action_id:

                    @loopingcall.RetryDecorator(max_retry_count=10,
                                                inc_sleep_time=2,
                                                max_sleep_time=60,
                                                exceptions=(TypeError))
                    def _get_creds(client, task_id, environment_id):
                        result = m_cli.actions.get_result(environment_id,
                                                          task_id)['result']
                        return result

                    task_id = m_cli.actions.call(environment_id, action_id)
                    result = _get_creds(m_cli, task_id, environment_id)

            if not result:
                LOG.warning(_LW("This application doesn't have action "
                                "getCredentials"))
                return exc.HTTPInternalServerError
        except KeyError:
            # NOTE(starodubcevna): In CF service broker API spec return
            # code for failed bind is not present, so we will return 500.
            LOG.warning(_LW("This application doesn't have actions at all"))
            return exc.HTTPInternalServerError

        if 'credentials' in list(result):
            return result
        else:
            return {'credentials': result}

    def unbind(self, req, instance_id, app_id):
        """Unsupported functionality

        murano doesn't support this kind of functionality, so we just need
        to create a stub where the call will come. We can't raise something
        like NotImplementedError because we will have problems on Cloud Foundry
        side. The best way now it to return empty dict which will be correct
        answer for Cloud Foundry.
        """

        return {}

    def get_last_operation(self):
        """Not implemented functionality

        For some reason it's difficult to provide a valid JSON with the
        response code which is needed for our broker to be true asynchronous.
        In that case last_operation API call is not supported.
        """

        raise NotImplementedError


def _get_muranoclient(token_id):

    artifacts_client = None
    if CONF.packages_opts.packages_service in ['glance', 'glare']:
        artifacts_client = _get_glareclient(token_id)

    murano_url = CONF.murano.url
    if not murano_url:
        LOG.error('No murano url is specified')

    return muranoclient.Client(1, murano_url, token=token_id,
                               artifacts_client=artifacts_client)


def _get_glareclient(token_id):
    glare_settings = CONF.glare

    url = glare_settings.url
    if not url:
        LOG.error('No glare url is specified')

    return glare_client.Client(
        endpoint=url, token=token_id,
        insecure=glare_settings.insecure,
        key_file=glare_settings.key_file or None,
        ca_file=glare_settings.ca_file or None,
        cert_file=glare_settings.cert_file or None,
        type_name='murano',
        type_version=1)


def create_session(client, environment_id):
    id = client.sessions.configure(environment_id).id
    return id


def create_resource():
    return wsgi.Resource(Controller())
