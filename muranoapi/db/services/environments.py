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

import jsonschema

from muranoapi.api.v1 import schemas
from muranoapi.common import rpc
from muranoapi.common import uuidutils
from muranoapi.db import models
from muranoapi.db.services import sessions
from muranoapi.db import session as db_session
from muranoapi.openstack.common import timeutils


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
        environment_params['tenant_id'] = tenant_id

        environment = models.Environment()
        environment.update(environment_params)

        unit = db_session.get_session()
        with unit.begin():
            unit.add(environment)

        #saving environment as Json to itself
        environment.update({"description": environment.to_dict()})
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

        rpc.conductor().handle_task(env)

        with unit.begin():
            unit.delete(environment)

    @staticmethod
    def get_environment_description(environment_id, session_id=None):
        """
        Returns environment description for specified environment. If session
        is specified and not in deploying state function returns modified
        environment description, otherwise returns actual environment desc.

        :param environment_id: Environment Id
        :param session_id: Session Id
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

        return env_description

    @staticmethod
    def save_environment_description(session_id, environment):
        """
        Saves environment description to specified session

        :param session_id: Session Id
        :param environment: Environment Description
        """
        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        EnvironmentServices.normalize(environment)
        jsonschema.validate(environment, schemas.ENV_SCHEMA)
        session.description = environment
        session.save(unit)

    @staticmethod
    def normalize(environment):
        if 'id' not in environment:
            environment['id'] = uuidutils.generate_uuid()

        if 'services' not in environment:
            return

        for service in environment['services']:
            if 'id' not in service:
                service['id'] = uuidutils.generate_uuid()

            if 'created' not in service:
                service['created'] = str(timeutils.utcnow())

            if 'updated' not in service:
                service['updated'] = str(timeutils.utcnow())

            if 'units' not in service:
                continue

            for idx, unit in enumerate(service['units']):
                if 'id' not in unit:
                    unit['id'] = uuidutils.generate_uuid()

                if 'name' not in unit:
                    unit['name'] = '{srv_name}_instance_{number}'.format(
                        srv_name=service['name'], number=idx
                    )
