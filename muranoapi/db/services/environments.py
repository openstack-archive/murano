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

from muranoapi.common import rpc
from muranoapi.common import uuidutils
from muranoapi.db import models
from muranoapi.db.services import sessions
from muranoapi.db import session as db_session


EnvironmentStatus = collections.namedtuple('EnvironmentStatus', [
    'ready', 'pending', 'deploying'
])(
    ready='ready', pending='pending', deploying='deploying'
)


class EnvironmentServices(object):
    @staticmethod
    def get_environments_by(filters):
        """
        Returns list of environments
        :param filters: property filters
        :return: Returns list of environments
        """
        unit = db_session.get_session()
        environments = unit.query(models.Environment).\
            filter_by(**filters).all()

        for env in environments:
            env['status'] = EnvironmentServices.get_status(env['id'])

        return environments

    @staticmethod
    def get_status(environment_id):
        """
        Environment can have one of three distinguished statuses:

         - Deploying: there is at least one session with status `deploying`;
         - Pending: there is at least one session with status `open`;
         - Ready: there is no sessions in status `deploying` or `open`.

        :param environment_id: Id of environment for which we checking status.
        :return: Environment status
        """
        #Deploying: there is at least one valid session with status `deploying`
        deploying = sessions.SessionServices.get_sessions(
            environment_id,
            sessions.SessionState.deploying)
        if len(deploying) > 0:
            return 'deploying'

        #Pending: there is at least one valid session with status `open`;
        open = sessions.SessionServices.get_sessions(
            environment_id,
            sessions.SessionState.open)
        if len(open) > 0:
            return 'pending'

        #Ready: there are no sessions in status `deploying` or `open`
        return 'ready'

    @staticmethod
    def create(environment_params, tenant_id):
        #tagging environment by tenant_id for later checks
        """
        Creates environment with specified params, in particular - name
        :param environment_params: Dict, e.g. {'name': 'env-name'}
        :param tenant_id: Tenant Id
        :return: Created Environment
        """

        objects = {'?': {
            'id': uuidutils.generate_uuid(),
        }}
        objects.update(environment_params)
        objects['?']['type'] = 'io.murano.Environment'
        environment_params['tenant_id'] = tenant_id

        data = {
            'Objects': objects,
            'Attributes': []
        }

        environment = models.Environment()
        environment.update(environment_params)

        unit = db_session.get_session()
        with unit.begin():
            unit.add(environment)

        #saving environment as Json to itself
        environment.update({'description': data})
        environment.save(unit)

        return environment

    @staticmethod
    def delete(environment_id, token):
        """
        Deletes environment and notify orchestration engine about deletion

        :param environment_id: Environment that is going to be deleted
        :param token: OpenStack auth token
        """
        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(environment_id)

        #preparing data for removal from conductor
        env = environment.description
        env['services'] = {}
        env['deleted'] = True

        #Set X-Auth-Token for conductor
        env['token'] = token

        rpc.engine().handle_task(env)

        with unit.begin():
            unit.delete(environment)

    @staticmethod
    def get_environment_description(environment_id, session_id=None,
                                    inner=True):
        """
        Returns environment description for specified environment. If session
        is specified and not in deploying state function returns modified
        environment description, otherwise returns actual environment desc.

        :param environment_id: Environment Id
        :param session_id: Session Id
        :param inner: return contents of environment rather than whole
         Object Model structure
        :return: Environment Description Object
        """
        unit = db_session.get_session()

        if session_id:
            session = unit.query(models.Session).get(session_id)
            if sessions.SessionServices.validate(session):
                if session.state != sessions.SessionState.deployed:
                    env_description = session.description
                else:
                    env = unit.query(models.Environment)\
                        .get(session.environment_id)
                    env_description = env.description
            else:
                env = unit.query(models.Environment)\
                    .get(session.environment_id)
                env_description = env.description
        else:
            env = (unit.query(models.Environment).get(environment_id))
            env_description = env.description

        if not inner:
            return env_description
        else:
            return env_description['Objects']

    @staticmethod
    def save_environment_description(session_id, environment, inner=True):
        """
        Saves environment description to specified session

        :param session_id: Session Id
        :param environment: Environment Description
        :param inner: save modifications to only content of environment
         rather than whole Object Model structure
        """
        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)
        if inner:
            data = session.description.copy()
            data['Objects'] = environment
            session.description = data
        else:
            session.description = environment
        session.save(unit)
