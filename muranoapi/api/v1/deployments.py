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

from muranoapi.openstack.common import wsgi
from muranoapi.db.models import Deployment, Status
from muranoapi.db.session import get_session
from muranoapi.openstack.common import log as logging
from sqlalchemy import desc

log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        unit = get_session()
        query = unit.query(Deployment) \
            .filter_by(environment_id=environment_id) \
            .order_by(desc(Deployment.created))
        result = query.all()
        deployments = [deployment.to_dict() for deployment in result]
        return {'deployments': deployments}

    def statuses(self, request, environment_id, deployment_id):
        unit = get_session()
        query = unit.query(Status) \
            .filter_by(deployment_id=deployment_id) \
            .order_by(Status.created)

        if 'service_id' in request.GET:
            service_id_set = set(request.GET.getall('service_id'))
            environment = unit.query(Deployment).get(deployment_id).description
            entity_ids = []
            if 'services' in environment:
                for service in environment['services']:
                    if service['id'] in service_id_set:
                        entity_ids.append(service['id'])
                        if 'units' in service:
                            unit_ids = [u['id'] for u in service['units']
                                        if 'id' in u]
                            entity_ids = entity_ids + unit_ids
            if entity_ids:
                query = query.filter(Status.entity_id.in_(entity_ids))
            else:
                return {'reports': None}

        result = query.all()
        return {'reports': [status.to_dict() for status in result]}


def create_resource():
    return wsgi.Resource(Controller())
