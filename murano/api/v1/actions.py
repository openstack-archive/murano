#    Copyright (c) 2014 Mirantis, Inc.
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

from murano.common import policy
from murano.common import wsgi
from murano.db import models
from murano.db.services import environments as envs
from murano.db.services import sessions
from murano.db import session as db_session
from murano.common.i18n import _LI, _LE, _
from murano.openstack.common import log as logging
from murano.services import actions
from murano.services import states


LOG = logging.getLogger(__name__)


class Controller(object):
    def _validate_environment(self, unit, request, environment_id):
        environment = unit.query(models.Environment).get(environment_id)

        if environment is None:
            LOG.info(_LI('Environment <EnvId {0}> '
                         'is not found').format(environment_id))
            raise exc.HTTPNotFound

        if environment.tenant_id != request.context.tenant:
            LOG.info(_LI('User is not authorized to access '
                         'this tenant resources.'))
            raise exc.HTTPUnauthorized

    def execute(self, request, environment_id, action_id, body):
        policy.check("execute_action", request.context, {})

        LOG.debug('Action:Execute <ActionId: {0}>'.format(action_id))

        unit = db_session.get_session()
        self._validate_environment(unit, request, environment_id)

        # no new session can be opened if environment has deploying status
        env_status = envs.EnvironmentServices.get_status(environment_id)
        if env_status in (states.EnvironmentStatus.DEPLOYING,
                          states.EnvironmentStatus.DELETING):
            LOG.info(_LI('Could not open session for environment <EnvId: {0}>,'
                         'environment has deploying '
                         'status.').format(environment_id))
            raise exc.HTTPForbidden()

        user_id = request.context.user
        session = sessions.SessionServices.create(environment_id, user_id)

        if not sessions.SessionServices.validate(session):
            LOG.error(_LE('Session <SessionId {0}> '
                          'is invalid').format(session.id))
            raise exc.HTTPForbidden()

        task_id = actions.ActionServices.execute(
            action_id, session, unit, request.context.auth_token, body or {})
        return {'task_id': task_id}

    def get_result(self, request, environment_id, task_id):
        policy.check("execute_action", request.context, {})

        LOG.debug('Action:GetResult <TaskId: {0}>'.format(task_id))

        unit = db_session.get_session()
        self._validate_environment(unit, request, environment_id)
        result = actions.ActionServices.get_result(environment_id, task_id,
                                                   unit)

        if result is not None:
            return result
        msg = (_('Result for task with environment_id: {} and '
                 'task_id: {} was not found.')
               .format(environment_id, task_id))

        LOG.error(msg)
        raise exc.HTTPNotFound(msg)


def create_resource():
    return wsgi.Resource(Controller())
