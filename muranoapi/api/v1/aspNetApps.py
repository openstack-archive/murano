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
#    under the License.from oslo.config import cfg

from muranoapi import utils
from muranoapi.api.v1 import save_draft, get_draft, get_service_status
from muranoapi.common import uuidutils
from muranoapi.openstack.common import wsgi, timeutils
from muranoapi.openstack.common import log as logging

log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        log.debug(_('AspNetApps:List <EnvId: {0}>'.format(environment_id)))

        draft = prepare_draft(get_draft(environment_id,
                                        request.context.session))

        for dc in draft['services']['aspNetApps']:
            dc['status'] = get_service_status(environment_id,
                                              request.context.session, dc)

        return {'aspNetApps': draft['services']['aspNetApps']}

    @utils.verify_session
    def create(self, request, environment_id, body):
        log.debug(_('AspNetApps:Create <EnvId: {0}, Body: {1}>'.
                    format(environment_id, body)))

        draft = get_draft(session_id=request.context.session)

        aspNetApp = body.copy()
        aspNetApp['id'] = uuidutils.generate_uuid()
        aspNetApp['created'] = str(timeutils.utcnow())
        aspNetApp['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in aspNetApp['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = aspNetApp['name'] + '_instance_' + str(unit_count)

        draft = prepare_draft(draft)
        draft['services']['aspNetApps'].append(aspNetApp)
        save_draft(request.context.session, draft)

        return aspNetApp

    @utils.verify_session
    def delete(self, request, environment_id, app_id):
        log.debug(_('AspNetApps:Delete <EnvId: {0}, Id: {1}>'.
                    format(environment_id, app_id)))

        draft = get_draft(session_id=request.context.session)

        elements = [service for service in draft['services']['aspNetApps'] if
                    service['id'] != app_id]
        draft['services']['aspNetApps'] = elements
        save_draft(request.context.session, draft)


def prepare_draft(draft):
    if not 'services' in draft:
        draft['services'] = {}

    if not 'aspNetApps' in draft['services']:
        draft['services']['aspNetApps'] = []

    return draft


def create_resource():
    return wsgi.Resource(Controller())
