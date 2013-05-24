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

from webob import exc
from muranoapi.db.models import Session, Status
from muranoapi.db.session import get_session
from muranoapi.db.services.sessions import SessionServices
from muranoapi.db.services.sessions import SessionState
from muranoapi.db.services.environments import EnvironmentServices
from muranoapi.db.services.environments import EnvironmentStatus
from muranoapi.openstack.common import wsgi
from muranoapi.openstack.common import log as logging

log = logging.getLogger(__name__)


class Controller(object):
    def configure(self, request, environment_id):
        log.debug(_('Session:Configure <EnvId: {0}>'.format(environment_id)))

        # no new session can be opened if environment has deploying status
        env_status = EnvironmentServices.get_status(environment_id)
        if env_status == EnvironmentStatus.deploying:
            log.info('Could not open session for environment <EnvId: {0}>,'
                     'environment has deploying '
                     'status.'.format(environment_id))
            raise exc.HTTPForbidden()

        user_id = request.context.user
        session = SessionServices.create(environment_id, user_id)

        return session.to_dict()

    def show(self, request, session_id):
        log.debug(_('Session:Show <SessionId: {0}>'.format(session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        user_id = request.context.user
        if session.user_id != user_id:
            log.info('User <UserId {0}> is not authorized to access '
                     'session <SessionId {1}>.'.format(user_id, session_id))
            raise exc.HTTPUnauthorized()

        if not SessionServices.validate(session):
            log.info('Session <SessionId {0}> is invalid'.format(session_id))
            raise exc.HTTPForbidden()

        return session.to_dict()

    def delete(self, request, session_id):
        log.debug(_('Session:Delete <SessionId: {0}>'.format(session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        user_id = request.context.user
        if session.user_id != user_id:
            log.info('User <UserId {0}> is not authorized to access '
                     'session <SessionId {1}>.'.format(user_id, session_id))
            raise exc.HTTPUnauthorized()

        if session.state == SessionState.deploying:
            log.info('Session <SessionId: {0}> is in deploying state and '
                     'could not be deleted'.format(session_id))
            raise exc.HTTPForbidden()

        with unit.begin():
            unit.delete(session)

        return None

    def deploy(self, request, session_id):
        log.debug(_('Session:Deploy <SessionId: {0}>'.format(session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        if not SessionServices.validate(session):
            log.info('Session <SessionId {0}> is invalid'.format(session_id))
            raise exc.HTTPForbidden()

        if session.state != SessionState.open:
            log.info('Session <SessionId {0}> is already deployed or '
                     'deployment is in progress'.format(session_id))
            raise exc.HTTPForbidden()

        SessionServices.deploy(session, request.context.auth_token)

    def reports(self, request, environment_id, session_id):
        log.debug(_('Session:Reports <EnvId: {0}, '
                    'SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        statuses = unit.query(Status).filter_by(session_id=session_id).all()
        result = statuses

        if 'service_id' in request.GET:
            service_id = request.GET['service_id']

            environment = unit.query(Session).get(session_id).description
            services = []
            if 'services' in environment and 'activeDirectories' in \
                    environment['services']:
                services += environment['services']['activeDirectories']

            if 'services' in environment and 'webServers' in \
                    environment['services']:
                services += environment['services']['webServers']

            if 'services' in environment and 'aspNetApps' in\
                    environment['services']:
                services += environment['services']['aspNetApps']

            service = [service for service in services
                       if service['id'] == service_id][0]

            if service:
                entities = [u['id'] for u in service['units']]
                entities.append(service_id)
                result = []
                for status in statuses:
                    if status.entity_id in entities:
                        result.append(status)

        return {'reports': [status.to_dict() for status in result]}


def create_resource():
    return wsgi.Resource(Controller())
