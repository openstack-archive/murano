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

from sqlalchemy import desc
from webob import exc

from muranoapi.common import utils
from muranoapi.db import models
from muranoapi.db.services import core_services
from muranoapi.db.services import environments as envs
from muranoapi.db import session as db_session
from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging
from muranoapi.openstack.common import wsgi


log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request):
        log.debug(_('Environments:List'))

        #Only environments from same tenant as user should be returned
        filters = {'tenant_id': request.context.tenant}
        environments = envs.EnvironmentServices.get_environments_by(filters)
        environments = [env.to_dict() for env in environments]

        return {"environments": environments}

    def create(self, request, body):
        log.debug(_('Environments:Create <Body {0}>'.format(body)))

        environment = envs.EnvironmentServices.create(body.copy(),
                                                      request.context.tenant)

        return environment.to_dict()

    def show(self, request, environment_id):
        log.debug(_('Environments:Show <Id: {0}>'.format(environment_id)))

        session = db_session.get_session()
        environment = session.query(models.Environment).get(environment_id)

        if environment is None:
            log.info('Environment <EnvId {0}> is not found'
                     .format(environment_id))
            raise exc.HTTPNotFound

        if environment.tenant_id != request.context.tenant:
            log.info(_('User is not authorized to access '
                       'this tenant resources.'))
            raise exc.HTTPUnauthorized

        env = environment.to_dict()
        env['status'] = envs.EnvironmentServices.get_status(env['id'])

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session

        #add services to env
        get_data = core_services.CoreServices.get_data
        env['services'] = get_data(environment_id, '/services', session_id)

        return env

    def update(self, request, environment_id, body):
        log.debug(_('Environments:Update <Id: {0}, '
                    'Body: {1}>'.format(environment_id, body)))

        session = db_session.get_session()
        environment = session.query(models.Environment).get(environment_id)

        if environment is None:
            log.info(_('Environment <EnvId {0}> is not '
                       'found'.format(environment_id)))
            raise exc.HTTPNotFound

        if environment.tenant_id != request.context.tenant:
            log.info(_('User is not authorized to access '
                       'this tenant resources.'))
            raise exc.HTTPUnauthorized

        environment.update(body)
        environment.save(session)

        return environment.to_dict()

    def delete(self, request, environment_id):
        log.debug(_('Environments:Delete <Id: {0}>'.format(environment_id)))

        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(environment_id)

        if environment is None:
            log.info(_('Environment <EnvId {0}> '
                       'is not found'.format(environment_id)))
            raise exc.HTTPNotFound

        if environment.tenant_id != request.context.tenant:
            log.info(_('User is not authorized to access '
                       'this tenant resources.'))
            raise exc.HTTPUnauthorized

        envs.EnvironmentServices.delete(environment_id,
                                        request.context.auth_token)

    def last(self, request, environment_id):
        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session
        services = core_services.CoreServices.get_data(environment_id,
                                                       '/services',
                                                       session_id)
        session = db_session.get_session()
        result = {}
        for service in services:
            service_id = service['id']
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
