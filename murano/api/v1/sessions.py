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

from oslo_log import log as logging
from webob import exc

from murano.api.v1 import request_statistics
from murano.common.i18n import _
from murano.common import wsgi
from murano.db import models
from murano.db.services import environments as envs
from murano.db.services import sessions
from murano.db import session as db_session
from murano.services import states
from murano.utils import check_env
from murano.utils import check_session

LOG = logging.getLogger(__name__)
API_NAME = 'Sessions'


class Controller(object):

    @request_statistics.stats_count(API_NAME, 'Create')
    def configure(self, request, environment_id):
        LOG.debug('Session:Configure <EnvId: {env_id}>'
                  .format(env_id=environment_id))

        check_env(request, environment_id)

        # No new session can be opened if environment has deploying or
        # deleting status.
        env_status = envs.EnvironmentServices.get_status(environment_id)
        if env_status in (states.EnvironmentStatus.DEPLOYING,
                          states.EnvironmentStatus.DELETING):
            msg = _('Could not open session for environment <EnvId: '
                    '{env_id}>, environment has deploying or '
                    'deleting status.').format(env_id=environment_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        user_id = request.context.user
        session = sessions.SessionServices.create(environment_id, user_id)

        return session.to_dict()

    @request_statistics.stats_count(API_NAME, 'Index')
    def show(self, request, environment_id, session_id):
        LOG.debug('Session:Show <SessionId: {id}>'.format(id=session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        check_session(request, environment_id, session, session_id)

        user_id = request.context.user

        if session.user_id != user_id:
            msg = _('User <UserId {usr_id}> is not authorized to access '
                    'session <SessionId {s_id}>.').format(usr_id=user_id,
                                                          s_id=session_id)
            LOG.error(msg)
            raise exc.HTTPUnauthorized(explanation=msg)

        if not sessions.SessionServices.validate(session):
            msg = _('Session <SessionId {0}> is invalid: environment has been '
                    'updated or updating right now with other session'
                    ).format(session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        return session.to_dict()

    @request_statistics.stats_count(API_NAME, 'Delete')
    def delete(self, request, environment_id, session_id):
        LOG.debug('Session:Delete <SessionId: {s_id}>'.format(s_id=session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        check_session(request, environment_id, session, session_id)

        user_id = request.context.user
        if session.user_id != user_id:
            msg = _('User <UserId {usr_id}> is not authorized to access '
                    'session <SessionId {s_id}>.').format(usr_id=user_id,
                                                          s_id=session_id)
            LOG.error(msg)
            raise exc.HTTPUnauthorized(explanation=msg)

        if session.state == states.SessionState.DEPLOYING:
            msg = _('Session <SessionId: {s_id}> is in deploying state '
                    'and could not be deleted').format(s_id=session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        with unit.begin():
            unit.delete(session)

        return None

    @request_statistics.stats_count(API_NAME, 'Deploy')
    def deploy(self, request, environment_id, session_id):
        LOG.debug('Session:Deploy <SessionId: {s_id}>'.format(s_id=session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        check_session(request, environment_id, session, session_id)

        if not sessions.SessionServices.validate(session):
            msg = _('Session <SessionId {0}> is invalid: environment has been '
                    'updated or updating right now with other session'
                    ).format(session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        if session.state != states.SessionState.OPENED:
            msg = _('Session <SessionId {s_id}> is already deployed or '
                    'deployment is in progress').format(s_id=session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        envs.EnvironmentServices.deploy(session,
                                        unit,
                                        request.context)


def create_resource():
    return wsgi.Resource(Controller())
