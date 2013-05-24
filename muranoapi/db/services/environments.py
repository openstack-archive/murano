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
from collections import namedtuple

from amqplib.client_0_8 import Message
import anyjson
import eventlet
from muranoapi.common import config
from muranoapi.db.models import Session, Environment
from muranoapi.db.session import get_session
from sessions import SessionServices, SessionState


amqp = eventlet.patcher.import_patched('amqplib.client_0_8')
rabbitmq = config.CONF.rabbitmq

EnvironmentStatus = namedtuple('EnvironmentStatus', [
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
        unit = get_session()
        environments = unit.query(Environment).filter_by(**filters)

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
        #Ready: there are no sessions in status `deploying` or `open`
        status = 'ready'

        #Deploying: there is at least one valid session with status `deploying`
        deploying = SessionServices.get_sessions(environment_id,
                                                 SessionState.deploying)
        if len(deploying) > 0:
            status = 'deploying'

        #Pending: there is at least one valid session with status `open`;
        open = SessionServices.get_sessions(environment_id, SessionState.open)
        if len(open) > 0:
            status = 'pending'

        return status

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

        environment = Environment()
        environment.update(environment_params)

        unit = get_session()
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
        unit = get_session()
        environment = unit.query(Environment).get(environment_id)

        with unit.begin():
            unit.delete(environment)

        #preparing data for removal from conductor
        env = environment.description
        env['services'] = {}
        env['deleted'] = True

        #Set X-Auth-Token for conductor
        env['token'] = token

        connection = amqp.Connection('{0}:{1}'.
                                     format(rabbitmq.host, rabbitmq.port),
                                     virtual_host=rabbitmq.virtual_host,
                                     userid=rabbitmq.login,
                                     password=rabbitmq.password,
                                     ssl=rabbitmq.use_ssl, insist=True)
        channel = connection.channel()
        channel.exchange_declare('tasks', 'direct', durable=True,
                                 auto_delete=False)

        channel.basic_publish(Message(body=anyjson.serialize(env)), 'tasks',
                              'tasks')

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
        unit = get_session()

        if session_id:
            session = unit.query(Session).get(session_id)
            if SessionServices.validate(session):
                if session.state != SessionState.deployed:
                    env_description = session.description
                else:
                    env = unit.query(Environment).get(session.environment_id)
                    env_description = env.description
            else:
                env = unit.query(Environment).get(session.environment_id)
                env_description = env.description
        else:
            env = (unit.query(Environment).get(environment_id))
            env_description = env.description

        return env_description

    @staticmethod
    def save_environment_description(session_id, environment):
        """
        Saves environment description to specified session

        :param session_id: Session Id
        :param environment: Environment Description
        """
        unit = get_session()
        session = unit.query(Session).get(session_id)

        session.description = environment
        session.save(unit)
