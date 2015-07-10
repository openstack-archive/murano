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

import re

from oslo.db import exception as db_exc
from sqlalchemy import desc
from webob import exc

from murano.api.v1 import request_statistics
from murano.api.v1 import sessions
from murano.common import policy
from murano.common import utils
from murano.common import wsgi
from murano.db import models
from murano.db.services import core_services
from murano.db.services import environments as envs
from murano.db import session as db_session
from murano.common.i18n import _, _LI
from murano.openstack.common import log as logging

LOG = logging.getLogger(__name__)

API_NAME = 'Environments'

VALID_NAME_REGEX = re.compile('^[a-zA-Z]+[\w-]*$')


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'Index')
    def index(self, request):
        LOG.debug('Environments:List')
        policy.check('list_environments', request.context)

        # Only environments from same tenant as user should be returned
        filters = {'tenant_id': request.context.tenant}
        environments = envs.EnvironmentServices.get_environments_by(filters)
        environments = [env.to_dict() for env in environments]

        return {"environments": environments}

    @request_statistics.stats_count(API_NAME, 'Create')
    def create(self, request, body):
        LOG.debug(u'Environments:Create <Body {0}>'.format(body))
        policy.check('create_environment', request.context)
        name = unicode(body['name'])
        if VALID_NAME_REGEX.match(name):
            try:
                environment = envs.EnvironmentServices.create(
                    body.copy(),
                    request.context)
            except db_exc.DBDuplicateEntry:
                msg = _('Environment with specified name already exists')
                LOG.exception(msg)
                raise exc.HTTPConflict(explanation=msg)
        else:
            msg = _('Environment name must contain only alphanumeric '
                    'or "_-." characters, must start with alpha')
            LOG.exception(msg)
            raise exc.HTTPClientError(explanation=msg)

        return environment.to_dict()

    @request_statistics.stats_count(API_NAME, 'Show')
    def show(self, request, environment_id):
        LOG.debug('Environments:Show <Id: {0}>'.format(environment_id))
        target = {"environment_id": environment_id}
        policy.check('show_environment', request.context, target)

        session = db_session.get_session()
        environment = session.query(models.Environment).get(environment_id)

        if environment is None:
            LOG.info(_LI('Environment <EnvId {0}> is not found').format(
                environment_id))
            raise exc.HTTPNotFound

        if environment.tenant_id != request.context.tenant:
            LOG.info(_LI('User is not authorized to access '
                         'this tenant resources.'))
            raise exc.HTTPUnauthorized

        env = environment.to_dict()
        env['status'] = envs.EnvironmentServices.get_status(env['id'])

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session

        # add services to env
        get_data = core_services.CoreServices.get_data
        env['services'] = get_data(environment_id, '/services', session_id)

        return env

    @request_statistics.stats_count(API_NAME, 'Update')
    def update(self, request, environment_id, body):
        LOG.debug('Environments:Update <Id: {0}, '
                  'Body: {1}>'.format(environment_id, body))
        target = {"environment_id": environment_id}
        policy.check('update_environment', request.context, target)

        session = db_session.get_session()
        environment = session.query(models.Environment).get(environment_id)

        if environment is None:
            LOG.info(_LI('Environment <EnvId {0}> not '
                         'found').format(environment_id))
            raise exc.HTTPNotFound

        if environment.tenant_id != request.context.tenant:
            LOG.info(_LI('User is not authorized to access '
                         'this tenant resources.'))
            raise exc.HTTPUnauthorized

        LOG.debug('ENV NAME: {0}>'.format(body['name']))
        if VALID_NAME_REGEX.match(str(body['name'])):
            environment.update(body)
            environment.save(session)
        else:
            msg = _('Environment name must contain only alphanumeric '
                    'or "_-." characters, must start with alpha')
            LOG.error(msg)
            raise exc.HTTPClientError(explanation=msg)

        return environment.to_dict()

    @request_statistics.stats_count(API_NAME, 'Delete')
    def delete(self, request, environment_id):
        LOG.debug('Environments:Delete <Id: {0}>'.format(environment_id))
        target = {"environment_id": environment_id}
        policy.check('delete_environment', request.context, target)
        sessions_controller = sessions.Controller()
        session = sessions_controller.configure(request, environment_id)
        session_id = session['id']
        envs.EnvironmentServices.delete(environment_id, session_id)
        sessions_controller.deploy(request, environment_id, session_id)

    @request_statistics.stats_count(API_NAME, 'LastStatus')
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


def create_resource():
    return wsgi.Resource(Controller())
