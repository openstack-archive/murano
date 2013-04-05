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

from glazierapi import utils
from glazierapi.api.v1 import save_draft, get_draft, get_service_status
from glazierapi.common import uuidutils
from glazierapi.openstack.common import wsgi, timeutils
from glazierapi.openstack.common import log as logging

log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        log.debug(_('ActiveDirectory:Index <EnvId: {0}>'.
                    format(environment_id)))

        draft = prepare_draft(get_draft(environment_id,
                                        request.context.session))

        for dc in draft['services']['activeDirectories']:
            dc['status'] = get_service_status(environment_id,
                                              request.context.session,
                                              dc)

        return {'activeDirectories': draft['services']['activeDirectories']}

    @utils.verify_session
    def create(self, request, environment_id, body):
        log.debug(_('ActiveDirectory:Create <EnvId: {0}, Body: {1}>'.
                    format(environment_id, body)))

        draft = get_draft(session_id=request.context.session)

        active_directory = body.copy()
        active_directory['id'] = uuidutils.generate_uuid()
        active_directory['created'] = str(timeutils.utcnow())
        active_directory['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in active_directory['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = 'dc{0}'.format(unit_count)

        draft = prepare_draft(draft)
        draft['services']['activeDirectories'].append(active_directory)
        save_draft(request.context.session, draft)

        return active_directory

    def delete(self, request, environment_id, active_directory_id):
        log.debug(_('ActiveDirectory:Delete <EnvId: {0}, Id: {1}>'.
                    format(environment_id, active_directory_id)))

        draft = get_draft(request.context.session)
        items = [service for service in draft['services']['activeDirectories']
                 if service['id'] != active_directory_id]
        draft['services']['activeDirectories'] = items
        save_draft(request.context.session, draft)


def prepare_draft(draft):
    if not 'services' in draft:
        draft['services'] = {}

    if not 'activeDirectories' in draft['services']:
        draft['services']['activeDirectories'] = []

    return draft


def create_resource():
    return wsgi.Resource(Controller())
