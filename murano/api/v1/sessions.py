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

from murano.api.v1 import request_statistics
from murano.common.i18n import _
from murano.common import wsgi
from murano.db import models
from murano.db.services import environments as envs
from murano.db.services import sessions
from murano.db import session as db_session
from murano.openstack.common import log as logging
from murano.services import states

LOG = logging.getLogger(__name__)
API_NAME = 'Sessions'


class Controller(object):

    def _check_environment(self, request, environment_id):
        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(environment_id)

        if environment is None:
            msg = _('Environment <EnvId {0}>'
                    ' is not found').format(environment_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        if environment.tenant_id != request.context.tenant:
            msg = _('User is not authorized to access '
                    'this tenant resources.')
            LOG.error(msg)
            raise exc.HTTPUnauthorized(explanation=msg)

    def _check_session(self, request, environment_id, session, session_id):
        if session is None:
            msg = _('Session <SessionId {0}> is not found').format(session_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        if session.environment_id != environment_id:
            msg = _('Session <SessionId {0}> is not tied with Environment '
                    '<EnvId {1}>').format(session_id, environment_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        self._check_environment(request, environment_id)

    @request_statistics.stats_count(API_NAME, 'Create')
    def configure(self, request, environment_id):
        LOG.debug('Session:Configure <EnvId: {0}>'.format(environment_id))

        self._check_environment(request, environment_id)

        # no new session can be opened if environment has deploying status
        env_status = envs.EnvironmentServices.get_status(environment_id)
        if env_status in (states.EnvironmentStatus.DEPLOYING,
                          states.EnvironmentStatus.DELETING):
            msg = _('Could not open session for environment <EnvId: {0}>,'
                    'environment has deploying status.').format(environment_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        user_id = request.context.user
        session = sessions.SessionServices.create(environment_id, user_id)

        return session.to_dict()

    @request_statistics.stats_count(API_NAME, 'Index')
    def show(self, request, environment_id, session_id):
        LOG.debug('Session:Show <SessionId: {0}>'.format(session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        self._check_session(request, environment_id, session, session_id)

        user_id = request.context.user
        msg = _('User <UserId {0}> is not authorized to access session'
                '<SessionId {1}>.').format(user_id, session_id)
        if session.user_id != user_id:
            LOG.error(msg)
            raise exc.HTTPUnauthorized(explanation=msg)

        if not sessions.SessionServices.validate(session):
            msg = _('Session <SessionId {0}> is invalid').format(session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        return session.to_dict()

    @request_statistics.stats_count(API_NAME, 'Delete')
    def delete(self, request, environment_id, session_id):
        LOG.debug('Session:Delete <SessionId: {0}>'.format(session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        self._check_session(request, environment_id, session, session_id)

        user_id = request.context.user
        if session.user_id != user_id:
            msg = _('User <UserId {0}> is not authorized to access session'
                    '<SessionId {1}>.').format(user_id, session_id)
            LOG.error(msg)
            raise exc.HTTPUnauthorized(explanation=msg)

        if session.state == states.SessionState.DEPLOYING:
            msg = _('Session <SessionId: {0}> is in deploying state and '
                    'could not be deleted').format(session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        with unit.begin():
            unit.delete(session)

        return None

    @request_statistics.stats_count(API_NAME, 'Deploy')
    def deploy(self, request, environment_id, session_id):
        LOG.debug('Session:Deploy <SessionId: {0}>'.format(session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        self._check_session(request, environment_id, session, session_id)

        if not sessions.SessionServices.validate(session):
            msg = _('Session <SessionId {0}> is invalid').format(session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        if session.state != states.SessionState.OPENED:
            msg = _('Session <SessionId {0}> is already deployed or '
                    'deployment is in progress').format(session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        envs.EnvironmentServices.deploy(session,
                                        unit,
                                        request.context.auth_token)


def create_resource():
    return wsgi.Resource(Controller())
