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


from keystoneclient import exceptions as ks_exceptions
from oslo_config import cfg
from oslo_log import log as logging
import six
import yaml

from murano.common import auth_utils
from murano.common import uuidutils
from murano.db import models
from murano.db.services import sessions
from murano.db import session as db_session
from murano.services import states

CONF = cfg.CONF

LOG = logging.getLogger(__name__)
DEFAULT_NETWORK_TYPES = {
    "nova": 'io.murano.resources.NovaNetwork',
    "neutron": 'io.murano.resources.NeutronNetwork'
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
            elif session.state == states.SessionState.DEPLOYED:
                break
        if has_opened:
            return states.EnvironmentStatus.PENDING

        return states.EnvironmentStatus.READY

    @staticmethod
    def create(environment_params, context):
        # tagging environment by tenant_id for later checks
        """Creates environment with specified params, in particular - name

           :param environment_params: Dict, e.g. {'name': 'env-name'}
           :param context: request context to get the tenant id and the token
           :return: Created Environment
        """
        objects = {'?': {
            'id': uuidutils.generate_uuid(),
        }}
        network_driver = EnvironmentServices.get_network_driver(context)
        objects.update(environment_params)
        if not objects.get('defaultNetworks'):
            objects['defaultNetworks'] = \
                EnvironmentServices.generate_default_networks(objects['name'],
                                                              network_driver)
        objects['?']['type'] = 'io.murano.Environment'
        objects['?']['metadata'] = {}

        data = {
            'Objects': objects,
            'Attributes': [],
            'project_id': context.tenant,
            'user_id': context.user
        }

        environment_params['tenant_id'] = context.tenant
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
           :param session_id: Session Id
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
    def generate_default_networks(env_name, network_driver):
        net_config = CONF.find_file(
            CONF.networking.network_config_file)
        if net_config:
            LOG.debug("Loading network configuration from file")
            with open(net_config) as f:
                data = yaml.safe_load(f)
                return EnvironmentServices._objectify(data, {
                    'ENV': env_name
                })

        network_type = DEFAULT_NETWORK_TYPES[network_driver]
        LOG.debug("Setting '{net_type}' as environment's "
                  "default network".format(net_type=network_type))
        return {
            'environment': {
                '?': {
                    'id': uuidutils.generate_uuid(),
                    'type': network_type
                },
                'name': env_name + '-network'
            },
            'flat': None
        }

    @staticmethod
    def deploy(session, unit, context):
        environment = unit.query(models.Environment).get(
            session.environment_id)

        if (session.description['Objects'] is None and
                'ObjectsCopy' not in session.description):
            EnvironmentServices.remove(session.environment_id)
        else:
            sessions.SessionServices.deploy(
                session, environment, unit, context)

    @staticmethod
    def _objectify(data, replacements):
        if isinstance(data, dict):
            if isinstance(data.get('?'), dict):
                data['?']['id'] = uuidutils.generate_uuid()
            result = {}
            for key, value in data.items():
                result[key] = EnvironmentServices._objectify(
                    value, replacements)
            return result
        elif isinstance(data, list):
            return [EnvironmentServices._objectify(v, replacements)
                    for v in data]
        elif isinstance(data, six.string_types):
            for key, value in replacements.items():
                data = data.replace('%' + key + '%', value)
        return data

    @staticmethod
    def get_network_driver(context):
        driver = CONF.networking.driver
        if driver:
            LOG.debug("Will use {} as a network driver".format(driver))
            return driver

        session = auth_utils.get_token_client_session(
            context.auth_token, context.tenant)
        try:
            session.get_endpoint(service_type='network')
        except ks_exceptions.EndpointNotFound:
            LOG.debug("Will use NovaNetwork as a network driver")
            return "nova"
        else:
            LOG.debug("Will use Neutron as a network driver")
            return "neutron"
