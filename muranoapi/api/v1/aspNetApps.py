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

from muranoapi import utils
from muranoapi.db.services.systemservices import SystemServices
from muranoapi.openstack.common import wsgi
from muranoapi.openstack.common import log as logging
from webob.exc import HTTPNotFound

log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        log.debug(_('AspNetApps:List <EnvId: {0}>'.format(environment_id)))

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session

        get = SystemServices.get_services

        services = get(environment_id, 'aspNetApps', session_id)
        return {'aspNetApps': services}

    @utils.verify_session
    def create(self, request, environment_id, body):
        log.debug(_('AspNetApps:Create <EnvId: {0}, Body: {1}>'.
                    format(environment_id, body)))

        session_id = request.context.session
        create = SystemServices.create_asp_application

        return create(body.copy(), session_id, environment_id)

    @utils.verify_session
    def delete(self, request, environment_id, app_id):
        log.debug(_('AspNetApps:Delete <EnvId: {0}, Id: {1}>'.
                    format(environment_id, app_id)))

        session_id = request.context.session
        delete = SystemServices.delete_service

        try:
            delete(app_id, 'aspNetApps', session_id, environment_id)
        except ValueError:
            raise HTTPNotFound()


def create_resource():
    return wsgi.Resource(Controller())
