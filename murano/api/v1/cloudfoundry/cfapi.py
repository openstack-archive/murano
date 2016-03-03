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

import json
import uuid

import muranoclient.client as client
from oslo_config import cfg
from oslo_log import log as logging
import six
from webob import response

from murano.common.i18n import _LI, _LW
from murano.common import wsgi
from murano.db.catalog import api as db_api
from murano.db.services import cf_connections as db_cf


cfapi_opts = [
    cfg.StrOpt('tenant', default='admin',
               help=('Tenant for service broker')),
    cfg.StrOpt('bind_host', default='localhost',
               help=('host for service broker')),
    cfg.StrOpt('bind_port', default='8083',
               help=('host for service broker')),
    cfg.StrOpt('auth_url', default='localhost:5000'),
    cfg.StrOpt('user_domain_name', default='default'),
    cfg.StrOpt('project_domain_name', default='default')]

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CONF.register_opts(cfapi_opts, group='cfapi')


class Controller(object):
    """WSGI controller for application catalog resource in Murano v1 API"""

    def _package_to_service(self, package):
        srv = {}
        srv['id'] = package.id
        srv['name'] = package.name
        if len(package.description) > 256:
            srv['description'] = u"{0} ...".format(package.description[:253])
        else:
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

        packages = db_api.package_search({'type': 'application'},
                                         req.context,
                                         catalog=True)
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
            tenant = req.headers['X-Project-Id']
            db_cf.set_tenant_for_org(org_guid, tenant)
            LOG.info(_LI("Cloud Foundry {org_id} mapped to tenant "
                         "{tenant_name}").format(org_id=org_guid,
                                                 tenant_name=tenant))

        token = req.headers['X-Auth-Token']
        m_cli = muranoclient(token)
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

        package = db_api.package_get(service_id, req.context)
        LOG.debug('Adding service {name}'.format(name=package.name))

        service = self._make_service(space_guid, package, plan_id)
        db_cf.set_instance_for_service(instance_id, service['?']['id'],
                                       environment_id, tenant)

        # NOTE(Kezar): Here we are going through JSON and add ids where
        # it's necessary. Before that we need to drop '?' key from parameters
        # dictionary as far it contains murano package related info which is
        # necessary in our scenario
        if '?' in parameters.keys():
            parameters.pop('?', None)
            LOG.warning(_LW("Incorrect input parameters. Package related "
                            "parameters shouldn't be passed through Cloud "
                            "Foundry"))
        params = [parameters]
        while params:
            a = params.pop()
            for k, v in six.iteritems(a):
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
        return response.Response(status=202, json_body={})

    def deprovision(self, req, instance_id):
        service = db_cf.get_service_for_instance(instance_id)
        if not service:
            return {}

        service_id = service.service_id
        environment_id = service.environment_id
        token = req.headers['X-Auth-Token']
        m_cli = muranoclient(token)

        session_id = create_session(m_cli, environment_id)
        m_cli.services.delete(environment_id, '/' + service_id, session_id)
        m_cli.sessions.deploy(environment_id, session_id)
        return response.Response(status=202, json_body={})

    def bind(self, req, body, instance_id, app_id):
        filtered = [u'?', u'instance']
        db_service = db_cf.get_service_for_instance(instance_id)
        if not db_service:
            return {}

        service_id = db_service.service_id
        environment_id = db_service.environment_id
        token = req.headers['X-Auth-Token']
        m_cli = muranoclient(token)

        session_id = create_session(m_cli, environment_id)
        env = m_cli.environments.get(environment_id, session_id)
        LOG.debug('Got environment {0}'.format(env))
        service = self._get_service(env, service_id)
        LOG.debug('Got service {0}'.format(service))
        credentials = {}
        for k, v in six.iteritems(service):
            if k not in filtered:
                credentials[k] = v

        return {'credentials': credentials}

    def unbind(self, req, instance_id, app_id):
        """Unsupported functionality

        murano doesn't support this kind of functionality, so we just need
        to create a stub where the call will come. We can't raise something
        like NotImplementedError because we will have problems on Cloud Foundry
        side. The best way now it to return empty dict which will be correct
        answer for Cloud Foundry.
        """

        return {}

    def get_last_operation(self, req, instance_id):
        service = db_cf.get_service_for_instance(instance_id)
        # NOTE(freerunner): Prevent code 500 if requested environment
        # already doesn't exist.
        if not service:
            LOG.warning(_LW('Requested service for instance {} is not found'))
            body = {}
            resp = response.Response(status=410, json_body=body)
            return resp
        env_id = service.environment_id
        token = req.headers["X-Auth-Token"]
        m_cli = muranoclient(token)

        # NOTE(starodubcevna): we can track only environment status. it's
        # murano API limitation.
        m_environment = m_cli.environments.get(env_id)
        if m_environment.status == 'ready':
            body = {'state': 'succeeded',
                    'description': 'operation succeed'}
            resp = response.Response(status=200, json_body=body)
        elif m_environment.status in ['pending', 'deleting', 'deploying']:
            body = {'state': 'in progress',
                    'description': 'operation in progress'}
            resp = response.Response(status=202, json_body=body)
        elif m_environment.status in ['deploy failure', 'delete failure']:
            body = {'state': 'failed',
                    'description': '{0}. Please correct it manually'.format(
                        m_environment.status)}
            resp = response.Response(status=200, json_body=body)
        return resp


def muranoclient(token_id):
    # TODO(starodubcevna): I guess it can be done better.
    endpoint = "http://{murano_host}:{murano_port}".format(
        murano_host=CONF.bind_host, murano_port=CONF.bind_port)
    insecure = False

    LOG.debug('murano client created. Murano::Client <Url: {endpoint}'.format(
        endpoint=endpoint))

    return client.Client(1, endpoint=endpoint, token=token_id,
                         insecure=insecure)


def create_session(client, environment_id):
    id = client.sessions.configure(environment_id).id
    return id


def create_resource():
    return wsgi.Resource(Controller(),
                         serializer=wsgi.ServiceBrokerResponseSerializer())
