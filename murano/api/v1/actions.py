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

from oslo_log import log as logging
from webob import exc

from murano.common import policy
from murano.common import wsgi
from murano.db.services import environments as envs
from murano.db.services import sessions
from murano.db import session as db_session
from murano.services import actions
from murano.services import states
from murano.utils import verify_env


LOG = logging.getLogger(__name__)


class Controller(object):

    @verify_env
    def execute(self, request, environment_id, action_id, body):
        policy.check("execute_action", request.context, {})

        LOG.debug('Action:Execute <ActionId: {0}>'.format(action_id))

        unit = db_session.get_session()

        # no new session can be opened if environment has deploying status
        env_status = envs.EnvironmentServices.get_status(environment_id)
        if env_status in (states.EnvironmentStatus.DEPLOYING,
                          states.EnvironmentStatus.DELETING):
            LOG.warning('Could not open session for environment '
                        '<EnvId: {id}>, environment has deploying '
                        'or deleting status.'.format(id=environment_id))
            raise exc.HTTPForbidden()

        user_id = request.context.user
        session = sessions.SessionServices.create(environment_id, user_id)

        if not sessions.SessionServices.validate(session):
            LOG.error('Session <SessionId {id}> '
                      'is invalid'.format(id=session.id))
            raise exc.HTTPForbidden()

        task_id = actions.ActionServices.execute(
            action_id, session, unit, request.context, body or {})
        return {'task_id': task_id}

    @verify_env
    def get_result(self, request, environment_id, task_id):
        policy.check("execute_action", request.context, {})

        LOG.debug('Action:GetResult <TaskId: {id}>'.format(id=task_id))

        unit = db_session.get_session()
        result = actions.ActionServices.get_result(environment_id, task_id,
                                                   unit)

        if result is not None:
            return result
        msg = ('Result for task with environment_id: {env_id} and task_id: '
               '{task_id} was not found.'.format(env_id=environment_id,
                                                 task_id=task_id))
        LOG.error(msg)
        raise exc.HTTPNotFound(msg)


def create_resource():
    return wsgi.Resource(Controller())
