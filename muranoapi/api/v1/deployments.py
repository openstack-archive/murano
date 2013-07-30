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
from muranoapi.common.utils import build_entity_map

from muranoapi.openstack.common import wsgi
from muranoapi.db.models import Deployment, Status, Environment
from muranoapi.db.session import get_session
from muranoapi.openstack.common import log as logging
from sqlalchemy import desc
from webob import exc

log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        unit = get_session()
        verify_and_get_env(unit, environment_id, request)
        query = unit.query(Deployment) \
            .filter_by(environment_id=environment_id) \
            .order_by(desc(Deployment.created))
        result = query.all()
        deployments = [set_dep_state(deployment, unit).to_dict() for deployment
                       in result]
        return {'deployments': deployments}

    def statuses(self, request, environment_id, deployment_id):
        unit = get_session()
        query = unit.query(Status) \
            .filter_by(deployment_id=deployment_id) \
            .order_by(Status.created)
        deployment = verify_and_get_deployment(unit, environment_id,
                                               deployment_id)

        if 'service_id' in request.GET:
            service_id_set = set(request.GET.getall('service_id'))
            environment = deployment.description
            entity_ids = []
            if 'services' in environment:
                for service in environment['services']:
                    if service['id'] in service_id_set:
                        id_map = build_entity_map(service)
                        entity_ids = entity_ids + id_map.keys()
            if entity_ids:
                query = query.filter(Status.entity_id.in_(entity_ids))
            else:
                return {'reports': []}

        result = query.all()
        return {'reports': [status.to_dict() for status in result]}


def verify_and_get_env(db_session, environment_id, request):
    environment = db_session.query(Environment).get(environment_id)
    if not environment:
        log.info('Environment with id {0} not found'.format(environment_id))
        raise exc.HTTPNotFound

    if environment.tenant_id != request.context.tenant:
        log.info('User is not authorized to access this tenant resources.')
        raise exc.HTTPUnauthorized
    return environment


def verify_and_get_deployment(db_session, environment_id, deployment_id):
    deployment = db_session.query(Deployment).get(deployment_id)
    if not deployment:
        log.info('Deployment with id {0} not found'.format(deployment_id))
        raise exc.HTTPNotFound
    if deployment.environment_id != environment_id:
        log.info('Deployment with id {0} not found'
                 ' in environment {1}'.format(deployment_id, environment_id))
        raise exc.HTTPBadRequest
    return deployment


def create_resource():
    return wsgi.Resource(Controller())


def set_dep_state(deployment, unit):
    num_errors = unit.query(Status).filter_by(level='error').count()
    num_warnings = unit.query(Status).filter_by(level='warning').count()
    if deployment.finished:
        if num_errors:
            deployment.state = 'completed_w_errors'
        elif num_warnings:
            deployment.state = 'completed_w_warnings'
        else:
            deployment.state = 'success'
    else:
        if num_errors:
            deployment.state = 'running_w_errors'
        elif num_warnings:
            deployment.state = 'running_w_warnings'
        else:
            deployment.state = 'running'
    return deployment
