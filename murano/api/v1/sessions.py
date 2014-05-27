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
from murano.db import models
from murano.db.services import environments as envs
from murano.db.services import sessions
from murano.db import session as db_session

from murano.openstack.common.gettextutils import _  # noqa
from murano.openstack.common import log as logging
from murano.openstack.common import wsgi


LOG = logging.getLogger(__name__)
API_NAME = 'Sessions'


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'Create')
    def configure(self, request, environment_id):
        LOG.debug('Session:Configure <EnvId: {0}>'.format(environment_id))

        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(environment_id)

        if environment is None:
            LOG.info(_('Environment <EnvId {0}> '
                       'is not found').format(environment_id))
            raise exc.HTTPNotFound

        if environment.tenant_id != request.context.tenant:
            LOG.info(_('User is not authorized to access '
                       'this tenant resources.'))
            raise exc.HTTPUnauthorized

        # no new session can be opened if environment has deploying status
        env_status = envs.EnvironmentServices.get_status(environment_id)
        if env_status == envs.EnvironmentStatus.deploying:
            LOG.info(_('Could not open session for environment <EnvId: {0}>,'
                       'environment has deploying '
                       'status.').format(environment_id))
            raise exc.HTTPForbidden()

        user_id = request.context.user
        session = sessions.SessionServices.create(environment_id, user_id)

        return session.to_dict()

    @request_statistics.stats_count(API_NAME, 'Index')
    def show(self, request, environment_id, session_id):
        LOG.debug('Session:Show <SessionId: {0}>'.format(session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        if session is None:
            LOG.error(_('Session <SessionId {0}> '
                        'is not found').format(session_id))
            raise exc.HTTPNotFound()

        if session.environment_id != environment_id:
            LOG.error(_('Session <SessionId {0}> is not tied with Environment '
                        '<EnvId {1}>').format(session_id, environment_id))
            raise exc.HTTPNotFound()

        user_id = request.context.user
        if session.user_id != user_id:
            LOG.error(_('User <UserId {0}> is not authorized to access session'
                        '<SessionId {1}>.').format(user_id, session_id))
            raise exc.HTTPUnauthorized()

        if not sessions.SessionServices.validate(session):
            LOG.error(_('Session <SessionId {0}> '
                        'is invalid').format(session_id))
            raise exc.HTTPForbidden()

        return session.to_dict()

    @request_statistics.stats_count(API_NAME, 'Delete')
    def delete(self, request, environment_id, session_id):
        LOG.debug('Session:Delete <SessionId: {0}>'.format(session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        if session is None:
            LOG.error(_('Session <SessionId {0}> '
                        'is not found').format(session_id))
            raise exc.HTTPNotFound()

        if session.environment_id != environment_id:
            LOG.error(_('Session <SessionId {0}> is not tied with Environment '
                        '<EnvId {1}>').format(session_id, environment_id))
            raise exc.HTTPNotFound()

        user_id = request.context.user
        if session.user_id != user_id:
            LOG.error(_('User <UserId {0}> is not authorized to access session'
                        '<SessionId {1}>.').format(user_id, session_id))
            raise exc.HTTPUnauthorized()

        if session.state == sessions.SessionState.deploying:
            LOG.error(_('Session <SessionId: {0}> is in deploying state and '
                        'could not be deleted').format(session_id))
            raise exc.HTTPForbidden()

        with unit.begin():
            unit.delete(session)

        return None

    @request_statistics.stats_count(API_NAME, 'Deploy')
    def deploy(self, request, environment_id, session_id):
        LOG.debug('Session:Deploy <SessionId: {0}>'.format(session_id))

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        if session is None:
            LOG.error(_('Session <SessionId {0}> '
                        'is not found').format(session_id))
            raise exc.HTTPNotFound()

        if session.environment_id != environment_id:
            LOG.error(_('Session <SessionId {0}> is not tied with Environment '
                        '<EnvId {1}>').format(session_id, environment_id))
            raise exc.HTTPNotFound()

        if not sessions.SessionServices.validate(session):
            LOG.error(_('Session <SessionId {0}> '
                        'is invalid').format(session_id))
            raise exc.HTTPForbidden()

        if session.state != sessions.SessionState.open:
            LOG.error(_('Session <SessionId {0}> is already deployed or '
                        'deployment is in progress').format(session_id))
            raise exc.HTTPForbidden()

        sessions.SessionServices.deploy(session,
                                        unit,
                                        request.context.auth_token)


def create_resource():
    return wsgi.Resource(Controller())
