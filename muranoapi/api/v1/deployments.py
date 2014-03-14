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

from muranoapi.api.v1 import statistics
from muranoapi.common import utils
from muranoapi.db import models
from muranoapi.db import session as db_session


from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging
from muranoapi.openstack.common import wsgi


log = logging.getLogger(__name__)

API_NAME = 'Deployments'


class Controller(object):
    @statistics.stats_count(API_NAME, 'Index')
    def index(self, request, environment_id):
        unit = db_session.get_session()
        verify_and_get_env(unit, environment_id, request)
        query = unit.query(models.Deployment) \
            .filter_by(environment_id=environment_id) \
            .order_by(desc(models.Deployment.created))
        result = query.all()
        deployments = [set_dep_state(deployment, unit).to_dict() for deployment
                       in result]
        return {'deployments': deployments}

    @statistics.stats_count(API_NAME, 'Statuses')
    def statuses(self, request, environment_id, deployment_id):
        unit = db_session.get_session()
        query = unit.query(models.Status) \
            .filter_by(deployment_id=deployment_id) \
            .order_by(models.Status.created)
        deployment = verify_and_get_deployment(unit, environment_id,
                                               deployment_id)

        if 'service_id' in request.GET:
            service_id_set = set(request.GET.getall('service_id'))
            environment = deployment.description
            entity_ids = []
            if 'services' in environment:
                for service in environment['services']:
                    if service['id'] in service_id_set:
                        id_map = utils.build_entity_map(service)
                        entity_ids = entity_ids + id_map.keys()
            if entity_ids:
                query = query.filter(models.Status.entity_id.in_(entity_ids))
            else:
                return {'reports': []}

        result = query.all()
        return {'reports': [status.to_dict() for status in result]}


def verify_and_get_env(db_session, environment_id, request):
    environment = db_session.query(models.Environment).get(environment_id)
    if not environment:
        log.info(_('Environment with id {0} not found'.format(environment_id)))
        raise exc.HTTPNotFound

    if environment.tenant_id != request.context.tenant:
        log.info(_('User is not authorized to access this tenant resources.'))
        raise exc.HTTPUnauthorized
    return environment


def verify_and_get_deployment(db_session, environment_id, deployment_id):
    deployment = db_session.query(models.Deployment).get(deployment_id)
    if not deployment:
        log.info(_('Deployment with id {0} not found'.format(deployment_id)))
        raise exc.HTTPNotFound
    if deployment.environment_id != environment_id:
        log.info(_('Deployment with id {0} not found'
                   ' in environment {1}'.format(deployment_id,
                                                environment_id)))
        raise exc.HTTPBadRequest
    return deployment


def create_resource():
    return wsgi.Resource(Controller())


def set_dep_state(deployment, unit):
    num_errors = unit.query(models.Status).filter_by(
        level='error',
        deployment_id=deployment.id).count()

    num_warnings = unit.query(models.Status).filter_by(
        level='warning',
        deployment_id=deployment.id).count()

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
