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

from oslo_config import cfg
from oslo_log import log as logging
import tenacity
from webob import response

from murano.common import auth_utils  # noqa
from murano.common import wsgi
from murano.db.services import cf_connections as db_cf
import muranoclient.client as muranoclient
from muranoclient.common import exceptions
from muranoclient.glance import client as glare_client


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


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
            srv['tags'].append(tag)
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

        token = req.headers['X-Auth-Token']
        m_cli = _get_muranoclient(token, req)
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
            tenant = req.headers['X-Project-Id']
            db_cf.set_tenant_for_org(org_guid, tenant)
            LOG.info("Cloud Foundry {org_id} mapped to tenant "
                     "{tenant_name}".format(org_id=org_guid,
                                            tenant_name=tenant))

        token = req.headers['X-Auth-Token']
        m_cli = _get_muranoclient(token, req)

        def _set_new_environment_for_space(space_guid, log_msg):
            body = {'name': 'my_{uuid}'.format(uuid=uuid.uuid4().hex)}
            env = m_cli.environments.create(body)
            db_cf.set_environment_for_space(space_guid, env.id)
            LOG.info(log_msg.format(space_id=space_guid,
                                    environment_id=env.id))
            return env.id

        try:
            environment_id = db_cf.get_environment_for_space(space_guid)
            # NOTE: Check that environment which was previously linked with
            # CF space still exist, reset a new environment for space.
            try:
                env = m_cli.environments.get(environment_id)
            except exceptions.HTTPNotFound:
                msg = ("Can not find environment_id {environment_id}, "
                       "will create a new one."
                       .format(environment_id=environment_id))
                LOG.info(msg)
                env = {}
            if not env:
                log_msg = ("Cloud Foundry {space_id} remapped to "
                           "{environment_id}")
                environment_id = _set_new_environment_for_space(
                    space_guid, log_msg)
        except AttributeError:
            log_msg = ("Cloud Foundry {space_id} mapped to "
                       "{environment_id}")
            environment_id = _set_new_environment_for_space(
                space_guid, log_msg)

        package = m_cli.packages.get(service_id)
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
            LOG.warning("Incorrect input parameters. Package related "
                        "parameters shouldn't be passed through Cloud "
                        "Foundry")
        params = [parameters]
        while params:
            a = params.pop()
            for k, v in a.items():
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
        m_cli = _get_muranoclient(token, req)

        session_id = create_session(m_cli, environment_id)
        m_cli.services.delete(environment_id, '/' + service_id, session_id)
        m_cli.sessions.deploy(environment_id, session_id)
        return response.Response(status=202, json_body={})

    def bind(self, req, body, instance_id, app_id):
        db_service = db_cf.get_service_for_instance(instance_id)
        if not db_service:
            return {}

        service_id = db_service.service_id
        environment_id = db_service.environment_id
        token = req.headers['X-Auth-Token']
        m_cli = _get_muranoclient(token, req)

        session_id = create_session(m_cli, environment_id)
        env = m_cli.environments.get(environment_id, session_id)
        LOG.debug('Got environment {0}'.format(env))
        service = self._get_service(env, service_id)
        LOG.debug('Got service {0}'.format(service))

        # NOTE(starodubcevna): Here we need to find an action which will return
        # us needed credentials. By default we will look for getCredentials
        # action.
        result = {}
        try:
            actions = service['?']['_actions']
            for action_id in list(actions):
                if 'getCredentials' in action_id:

                    @tenacity.retry(
                        retry=tenacity.retry_if_exception_type(TypeError),
                        wait=tenacity.wait_random(min=1, max=10),
                        stop=tenacity.stop_after_delay(30),
                        reraise=True)
                    def _get_creds(client, task_id, environment_id):
                        result = m_cli.actions.get_result(environment_id,
                                                          task_id)['result']
                        return result

                    task_id = m_cli.actions.call(environment_id, action_id)
                    result = _get_creds(m_cli, task_id, environment_id)

            if not result:
                LOG.warning("This application doesn't have action "
                            "getCredentials")
                return response.Response(status=500)
        except KeyError:
            # NOTE(starodubcevna): In CF service broker API spec return
            # code for failed bind is not present, so we will return 500.
            LOG.warning("This application doesn't have actions at all")
            return response.Response(status=500)

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

    def get_last_operation(self, req, instance_id):
        service = db_cf.get_service_for_instance(instance_id)
        # NOTE(freerunner): Prevent code 500 if requested environment
        # already doesn't exist.
        if not service:
            LOG.warning('Requested service for instance {0} is not '
                        'found'.format(instance_id))
            body = {}
            resp = response.Response(status=410, json_body=body)
            return resp
        env_id = service.environment_id
        token = req.headers["X-Auth-Token"]
        m_cli = _get_muranoclient(token, req)

        # NOTE(starodubcevna): we can track only environment status. it's
        # murano API limitation.
        m_environment = m_cli.environments.get(env_id)
        body = {'state': 'unknown', 'description': 'operation unknown'}
        resp = response.Response(status=500, json_body=body)
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


def _get_muranoclient(token_id, req):

    artifacts_client = None
    if CONF.engine.packages_service in ['glance', 'glare']:
        artifacts_client = _get_glareclient(token_id, req)

    murano_url = CONF.murano.url or req.endpoints.get('murano')
    if not murano_url:
        LOG.error('No murano url is specified and no '
                  '"application-catalog" '
                  'service is registered in keystone.')

    return muranoclient.Client(1, murano_url, token=token_id,
                               artifacts_client=artifacts_client)


def _get_glareclient(token_id, req):
    glare_settings = CONF.glare

    url = glare_settings.url or req.endpoints.get('glare')
    if not url:
        LOG.error('No glare url is specified and no "artifact" '
                  'service is registered in keystone.')
    # TODO(gyurco): use auth_utils.get_session_client_parameters
    return glare_client.Client(
        endpoint=url, token=token_id,
        insecure=glare_settings.insecure,
        key_file=glare_settings.keyfile or None,
        ca_file=glare_settings.cafile or None,
        cert_file=glare_settings.certfile or None,
        type_name='murano',
        type_version=1)


def create_session(client, environment_id):
    id = client.sessions.configure(environment_id).id
    return id


def create_resource():
    return wsgi.Resource(Controller(),
                         serializer=wsgi.ServiceBrokerResponseSerializer())
