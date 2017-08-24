#    Copyright (c) 2013 Mirantis, Inc.
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

import datetime

import jsonpatch
from oslo_db import exception as db_exc
from oslo_log import log as logging
import six
from sqlalchemy import desc
from webob import exc

from murano.api.v1 import request_statistics
from murano.api.v1 import sessions
from murano.common.i18n import _
from murano.common import policy
from murano.common import utils
from murano.common import wsgi
from murano.db import models
from murano.db.services import core_services
from murano.db.services import environments as envs
from murano.db.services import sessions as session_services
from murano.db import session as db_session
from murano.engine.system import status_reporter
from murano.services import states
from murano.utils import check_env
from murano.utils import check_session
from murano.utils import verify_env

LOG = logging.getLogger(__name__)

API_NAME = 'Environments'


class Controller(object):

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self._notifier = status_reporter.Notification()

    @request_statistics.stats_count(API_NAME, 'Index')
    def index(self, request):
        all_tenants = request.GET.get('all_tenants', 'false').lower() == 'true'
        tenant = request.GET.get('tenant', None)
        LOG.debug('Environments:List <all_tenants: {tenants}, '
                  'tenant: {tenant}>'.format(tenants=all_tenants,
                                             tenant=tenant))

        if all_tenants:
            policy.check('list_environments_all_tenants', request.context)
            filters = {}
        elif tenant:
            policy.check('list_environments_all_tenants', request.context)
            filters = {'tenant_id': tenant}
        else:
            policy.check('list_environments', request.context)
            # Only environments from same tenant as user should be returned
            filters = {'tenant_id': request.context.tenant}

        environments = envs.EnvironmentServices.get_environments_by(filters)
        environments = [env.to_dict() for env in environments]

        return {"environments": environments}

    @request_statistics.stats_count(API_NAME, 'Create')
    def create(self, request, body):
        LOG.debug('Environments:Create <Body {body}>'.format(body=body))
        policy.check('create_environment', request.context)

        if not('name' in body and body['name'].strip()):
            msg = _('Please, specify a name of the environment to create')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)

        name = six.text_type(body['name'])
        if len(name) > 255:
            msg = _('Environment name should be 255 characters maximum')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)
        try:
            environment = envs.EnvironmentServices.create(
                body.copy(),
                request.context)
        except db_exc.DBDuplicateEntry:
            msg = _('Environment with specified name already exists')
            LOG.error(msg)
            raise exc.HTTPConflict(explanation=msg)

        return environment.to_dict()

    @request_statistics.stats_count(API_NAME, 'Show')
    @verify_env
    def show(self, request, environment_id):
        LOG.debug('Environments:Show <Id: {id}>'.format(id=environment_id))
        target = {"environment_id": environment_id}
        policy.check('show_environment', request.context, target)

        session = db_session.get_session()
        environment = session.query(models.Environment).get(environment_id)
        env = environment.to_dict()
        env['status'] = envs.EnvironmentServices.get_status(env['id'])

        # if env is currently being deployed we can provide information about
        # the session right away
        env['acquired_by'] = None
        if env['status'] == states.EnvironmentStatus.DEPLOYING:
            session_list = session_services.SessionServices.get_sessions(
                environment_id, state=states.SessionState.DEPLOYING)
            if session_list:
                env['acquired_by'] = session_list[0].id

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session
        if session_id:
            env_session = session.query(models.Session).get(session_id)
            check_session(request, environment_id, env_session, session_id)

        # add services to env
        get_data = core_services.CoreServices.get_data
        env['services'] = get_data(environment_id, '/services', session_id)

        return env

    @request_statistics.stats_count(API_NAME, 'Update')
    @verify_env
    def update(self, request, environment_id, body):
        """"Rename an environment."""
        LOG.debug('Environments:Update <Id: {id}, '
                  'Body: {body}>'.format(id=environment_id, body=body))
        target = {"environment_id": environment_id}
        policy.check('update_environment', request.context, target)

        session = db_session.get_session()
        environment = session.query(models.Environment).get(environment_id)
        new_name = six.text_type(body['name'])
        if new_name.strip():
            if len(new_name) > 255:
                msg = _('Environment name should be 255 characters maximum')
                LOG.error(msg)
                raise exc.HTTPBadRequest(explanation=msg)
            try:
                environment.update({'name': new_name})
                environment.save(session)
            except db_exc.DBDuplicateEntry:
                msg = _('Environment with specified name already exists')
                LOG.error(msg)
                raise exc.HTTPConflict(explanation=msg)
        else:
            msg = _('Environment name must contain at least one '
                    'non-white space symbol')
            LOG.error(msg)
            raise exc.HTTPClientError(explanation=msg)

        return environment.to_dict()

    @request_statistics.stats_count(API_NAME, 'Delete')
    def delete(self, request, environment_id):
        target = {"environment_id": environment_id}
        policy.check('delete_environment', request.context, target)
        environment = check_env(request, environment_id)

        if request.GET.get('abandon', '').lower() == 'true':
            LOG.debug(
                'Environments:Abandon  <Id: {id}>'.format(id=environment_id))
            envs.EnvironmentServices.remove(environment_id)
        else:
            LOG.debug(
                'Environments:Delete <Id: {id}>'.format(id=environment_id))
            sessions_controller = sessions.Controller()
            session = sessions_controller.configure(
                request, environment_id)
            session_id = session['id']
            envs.EnvironmentServices.delete(environment_id, session_id)
            sessions_controller.deploy(request, environment_id, session_id)

        env = environment.to_dict()
        env['deleted'] = datetime.datetime.utcnow()
        self._notifier.report('environment.delete.end', env)

    @request_statistics.stats_count(API_NAME, 'LastStatus')
    @verify_env
    def last(self, request, environment_id):
        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session
        services = core_services.CoreServices.get_data(environment_id,
                                                       '/services',
                                                       session_id)
        session = db_session.get_session()
        result = {}
        for service in services or []:
            service_id = service['?']['id']
            entity_ids = utils.build_entity_map(service).keys()
            last_status = session.query(models.Status). \
                filter(models.Status.entity_id.in_(entity_ids)). \
                order_by(desc(models.Status.created)). \
                first()
            if last_status:
                result[service_id] = last_status.to_dict()
            else:
                result[service_id] = None
        return {'lastStatuses': result}

    @request_statistics.stats_count(API_NAME, 'GetModel')
    @verify_env
    def get_model(self, request, environment_id, path):
        LOG.debug('Environments:GetModel <Id: %(env_id)s>, Path: %(path)s',
                  {'env_id': environment_id, 'path': path})
        target = {"environment_id": environment_id}
        policy.check('show_environment', request.context, target)

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session

        get_description = envs.EnvironmentServices.get_environment_description
        env_model = get_description(environment_id, session_id)
        try:
            result = utils.TraverseHelper.get(path, env_model)
        except (KeyError, ValueError):
            raise exc.HTTPNotFound

        return result

    @request_statistics.stats_count(API_NAME, 'UpdateModel')
    @verify_env
    def update_model(self, request, environment_id, body=None):
        if not body:
            msg = _('Request body is empty: please, provide '
                    'environment object model patch')
            LOG.error(msg)
            raise exc.HTTPBadRequest(msg)
        LOG.debug('Environments:UpdateModel <Id: %(env_id)s, Body: %(body)s>',
                  {'env_id': environment_id, 'body': body})
        target = {"environment_id": environment_id}
        policy.check('update_environment', request.context, target)

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session

        get_description = envs.EnvironmentServices.get_environment_description
        env_model = get_description(environment_id, session_id)

        for change in body:
            change['path'] = '/' + '/'.join(change['path'])

        patch = jsonpatch.JsonPatch(body)
        try:
            patch.apply(env_model, in_place=True)
        except jsonpatch.JsonPatchException as e:
            raise exc.HTTPNotFound(str(e))

        save_description = envs.EnvironmentServices. \
            save_environment_description
        save_description(session_id, env_model)

        return env_model


def create_resource():
    return wsgi.Resource(Controller())
