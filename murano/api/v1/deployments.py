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

from murano.api.v1 import request_statistics
from murano.common.helpers import token_sanitizer
from murano.common.i18n import _LI
from murano.common import policy
from murano.common import utils
from murano.common import wsgi
from murano.db import models
from murano.db import session as db_session
from murano.openstack.common import log as logging

LOG = logging.getLogger(__name__)

API_NAME = 'Deployments'


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'Index')
    def index(self, request, environment_id):
        target = {"environment_id": environment_id}
        policy.check("list_deployments", request.context, target)

        unit = db_session.get_session()
        verify_and_get_env(unit, environment_id, request)
        query = unit.query(models.Task) \
            .filter_by(environment_id=environment_id) \
            .order_by(desc(models.Task.created))
        result = query.all()
        deployments = [set_dep_state(deployment, unit).to_dict() for deployment
                       in result]
        return {'deployments': deployments}

    @request_statistics.stats_count(API_NAME, 'Statuses')
    def statuses(self, request, environment_id, deployment_id):
        target = {"environment_id": environment_id,
                  "deployment_id": deployment_id}
        policy.check("statuses_deployments", request.context, target)

        unit = db_session.get_session()
        query = unit.query(models.Status) \
            .filter_by(task_id=deployment_id) \
            .order_by(models.Status.created)
        deployment = verify_and_get_deployment(unit, environment_id,
                                               deployment_id)

        if 'service_id' in request.GET:
            service_id_set = set(request.GET.getall('service_id'))
            environment = deployment.description
            entity_ids = []
            for service in environment.get('services', []):
                if service['?']['id'] in service_id_set:
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
        LOG.info(_LI(
            'Environment with id {0} not found').format(environment_id))
        raise exc.HTTPNotFound

    if environment.tenant_id != request.context.tenant:
        LOG.info(_LI(
            'User is not authorized to access this tenant resources.'))
        raise exc.HTTPUnauthorized
    return environment


def _patch_description(description):
    description['services'] = description.pop('applications', [])
    return token_sanitizer.TokenSanitizer().sanitize(description)


def verify_and_get_deployment(db_session, environment_id, deployment_id):
    deployment = db_session.query(models.Task).get(deployment_id)
    if not deployment:
        LOG.info(_LI('Deployment with id {0} not found').format(deployment_id))
        raise exc.HTTPNotFound
    if deployment.environment_id != environment_id:
        LOG.info(_LI('Deployment with id {0} not found'
                     ' in environment {1}').format(deployment_id,
                                                   environment_id))
        raise exc.HTTPBadRequest

    deployment.description = _patch_description(deployment.description)
    return deployment


def create_resource():
    return wsgi.Resource(Controller())


def set_dep_state(deployment, unit):
    num_errors = unit.query(models.Status).filter_by(
        level='error',
        task_id=deployment.id).count()

    num_warnings = unit.query(models.Status).filter_by(
        level='warning',
        task_id=deployment.id).count()

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

    deployment.description = _patch_description(deployment.description)
    return deployment
