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
import collections

from muranoapi.common.helpers import token_sanitizer
from muranoapi.common import rpc
from muranoapi.db import models
from muranoapi.db import session as db_session


SessionState = collections.namedtuple('SessionState', [
    'open', 'deploying', 'deployed'
])(
    open='open', deploying='deploying', deployed='deployed'
)


class SessionServices(object):
    @staticmethod
    def get_sessions(environment_id, state=None):
        """
        Get list of sessions for specified environment

        :param environment_id: Environment Id
        :param state: glazierapi.db.services.environments.EnvironmentStatus
        :return: Sessions for specified Environment, if SessionState is
        not defined all sessions for specified environment is returned.
        """

        unit = db_session.get_session()
        # Here we duplicate logic for reducing calls to database
        # Checks for validation is same as in validate.
        environment = unit.query(models.Environment).get(environment_id)

        return unit.query(models.Session).filter(
            #Get all session for this environment
            models.Session.environment_id == environment_id,
            #in this state, if state is not specified return in all states
            models.Session.state.in_(SessionState
                                     if state is None else [state]),
            #Only sessions with same version as current env version are valid
            models.Session.version == environment.version
        ).all()

    @staticmethod
    def create(environment_id, user_id):
        """
        Creates session object for specific environment for specified user.

        :param environment_id: Environment Id
        :param user_id: User Id
        :return: Created session
        """
        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(environment_id)

        session = models.Session()
        session.environment_id = environment.id
        session.user_id = user_id
        session.state = SessionState.open
        # used for checking if other sessions was deployed before this one
        session.version = environment.version
        # all changes to environment is stored here, and translated to
        # environment only after deployment completed
        session.description = environment.description

        with unit.begin():
            unit.add(session)

        return session

    @staticmethod
    def validate(session):
        """
        Session is valid only if no other session for same
        environment was already deployed on in deploying state,

        :param session: Session for validation
        """

        #if other session is deploying now current session is invalid
        unit = db_session.get_session()

        #if environment version is higher then version on which current session
        #is created then other session was already deployed
        current_env = unit.query(models.Environment).\
            get(session.environment_id)
        if current_env.version > session.version:
            return False

        #if other session is deploying now current session is invalid
        other_is_deploying = unit.query(models.Session).filter_by(
            environment_id=session.environment_id, state=SessionState.deploying
        ).count() > 0
        if session.state == SessionState.open and other_is_deploying:
            return False

        return True

    @staticmethod
    def deploy(session, unit, token):
        """
        Prepares environment for deployment and send deployment command to
        orchestration engine

        :param session: session that is going to be deployed
        :param unit: SQLalchemy session
        :param token: auth token that is going to be used by orchestration
        """
        #unit = get_session()

        #Set X-Auth-Token for conductor
        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(
            session.environment_id)

        data = {
            'model': session.description,
            'token': token,
            'tenant_id': environment.tenant_id
        }

        data['model']['Objects']['?']['id'] = environment.id
        data['model']['Objects']['applications'] = \
            data['model']['Objects'].get('services', [])

        if 'services' in data['model']['Objects']:
            del data['model']['Objects']['services']

        session.state = SessionState.deploying
        deployment = models.Deployment()
        deployment.environment_id = session.environment_id
        deployment.description = token_sanitizer.TokenSanitizer().sanitize(
            dict(session.description.get('Objects')))
        status = models.Status()
        status.text = "Deployment scheduled"
        status.level = "info"
        deployment.statuses.append(status)

        with unit.begin():
            unit.add(session)
            unit.add(deployment)

        rpc.engine().handle_task(data)
