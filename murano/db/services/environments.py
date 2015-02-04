# Copyright (c) 2013 Mirantis, Inc.
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

from murano.common import uuidutils
from murano.db import models
from murano.db.services import sessions
from murano.db import session as db_session
from murano.services import states


DEFAULT_NETWORKS = {
    'environment': 'io.murano.resources.NeutronNetwork',
    # 'flat': 'io.murano.resources.ExistingNetworkConnector'
}


class EnvironmentServices(object):
    @staticmethod
    def get_environments_by(filters):
        """Returns list of environments
           :param filters: property filters
           :return: Returns list of environments
        """
        unit = db_session.get_session()
        environments = unit.query(models.Environment). \
            filter_by(**filters).all()

        for env in environments:
            env['status'] = EnvironmentServices.get_status(env['id'])

        return environments

    @staticmethod
    def get_status(environment_id):
        """Environment can have one of the following statuses:

         - deploying: there is ongoing deployment for environment
         - deleting: environment is currently being deleted
         - deploy failure: last deployment session has failed
         - delete failure: last delete session has failed
         - pending: there is at least one session with status `open` and no
            errors in previous sessions
         - ready: there are no sessions for environment

        :param environment_id: Id of environment for which we checking status.
        :return: Environment status
        """
        # Deploying: there is at least one valid session with status deploying
        session_list = sessions.SessionServices.get_sessions(environment_id)
        has_opened = False
        for session in session_list:
            if session.state == states.SessionState.DEPLOYING:
                return states.EnvironmentStatus.DEPLOYING
            elif session.state == states.SessionState.DELETING:
                return states.EnvironmentStatus.DELETING
            elif session.state == states.SessionState.DEPLOY_FAILURE:
                return states.EnvironmentStatus.DEPLOY_FAILURE
            elif session.state == states.SessionState.DELETE_FAILURE:
                return states.EnvironmentStatus.DELETE_FAILURE
            elif session.state == states.SessionState.OPENED:
                has_opened = True
        if has_opened:
            return states.EnvironmentStatus.PENDING

        return states.EnvironmentStatus.READY

    @staticmethod
    def create(environment_params, tenant_id):
        # tagging environment by tenant_id for later checks
        """Creates environment with specified params, in particular - name

           :param environment_params: Dict, e.g. {'name': 'env-name'}
           :param tenant_id: Tenant Id
           :return: Created Environment
        """

        objects = {'?': {
            'id': uuidutils.generate_uuid(),
        }}
        objects.update(environment_params)
        objects.update(
            EnvironmentServices.generate_default_networks(objects['name']))
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

        # saving environment as Json to itself
        environment.update({'description': data})
        environment.save(unit)

        return environment

    @staticmethod
    def delete(environment_id, session_id):
        """Deletes environment and notify orchestration engine about deletion

           :param environment_id: Environment that is going to be deleted
           :param token: OpenStack auth token
        """

        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id, False)
        env_description['Objects'] = None
        EnvironmentServices.save_environment_description(
            session_id, env_description, False)

    @staticmethod
    def remove(environment_id):
        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(environment_id)
        if environment:
            with unit.begin():
                unit.delete(environment)

    @staticmethod
    def get_environment_description(environment_id, session_id=None,
                                    inner=True):
        """Returns environment description for specified environment.

           If session is specified and not in deploying state function
           returns modified environment description,
           otherwise returns actual environment desc.

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
                if session.state != states.SessionState.DEPLOYED:
                    env_description = session.description
                else:
                    env = unit.query(models.Environment) \
                        .get(session.environment_id)
                    env_description = env.description
            else:
                env = unit.query(models.Environment) \
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
        """Saves environment description to specified session.

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

    @staticmethod
    def generate_default_networks(env_name):
        # TODO(ativelkov):
        # This is a temporary workaround. Need to find a better way:
        # These objects have to be created in runtime when the environment is
        # deployed for the first time. Currently there is no way to persist
        # such changes, so we have to create the objects on the API side
        return {
            'defaultNetworks': {
                'environment': {
                    '?': {
                        'id': uuidutils.generate_uuid(),
                        'type': DEFAULT_NETWORKS['environment']
                    },
                    'name': env_name + '-network'
                },
                'flat': None
            }
        }

    @staticmethod
    def deploy(session, unit, token):
        environment = unit.query(models.Environment).get(
            session.environment_id)

        if (session.description['Objects'] is None and
                'ObjectsCopy' not in session.description):
            EnvironmentServices.remove(session.environment_id)
        else:
            sessions.SessionServices.deploy(session, environment, unit, token)
