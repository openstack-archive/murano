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
#    under the License.from oslo.config import cfg

from amqplib.client_0_8 import Message
import anyjson
import eventlet
from webob import exc
from glazierapi.common import config
from glazierapi.db.models import Session, Status, Environment
from glazierapi.db.session import get_session
from glazierapi.openstack.common import wsgi
from glazierapi.openstack.common import log as logging

amqp = eventlet.patcher.import_patched('amqplib.client_0_8')
rabbitmq = config.CONF.rabbitmq
log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        log.debug(_('Session:List <EnvId: {0}>'.format(environment_id)))

        filters = {'environment_id': environment_id,
                   'user_id': request.context.user}

        unit = get_session()
        configuration_sessions = unit.query(Session).filter_by(**filters)

        sessions = [session.to_dict() for session in configuration_sessions if
                    session.environment.tenant_id == request.context.tenant]
        return {"sessions": sessions}

    def configure(self, request, environment_id):
        log.debug(_('Session:Configure <EnvId: {0}>'.format(environment_id)))

        params = {'environment_id': environment_id,
                  'user_id': request.context.user, 'state': 'open'}

        session = Session()
        session.update(params)

        unit = get_session()
        if unit.query(Session).filter(
                Session.environment_id == environment_id and
                Session.state.in_(['open', 'deploying'])
        ).first():
            log.info('There is already open session for this environment')
            raise exc.HTTPConflict

        #create draft for apply later changes
        environment = unit.query(Environment).get(environment_id)
        session.description = environment.description

        with unit.begin():
            unit.add(session)

        return session.to_dict()

    def show(self, request, environment_id, session_id):
        log.debug(_('Session:Show <EnvId: {0}, '
                    'SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        if session.environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        return session.to_dict()

    def delete(self, request, environment_id, session_id):
        log.debug(_('Session:Delete <EnvId: {0}, '
                    'SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        comment = 'Session object in \'deploying\' state could not be deleted'
        if session.state == 'deploying':
            log.info(comment)
            raise exc.HTTPForbidden(comment=comment)

        with unit.begin():
            unit.delete(session)

        return None

    def reports(self, request, environment_id, session_id):
        log.debug(_('Session:Reports <EnvId: {0}, '
                    'SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        statuses = unit.query(Status).filter_by(session_id=session_id).all()
        result = statuses

        if 'service_id' in request.GET:
            service_id = request.GET['service_id']

            environment = unit.query(Session).get(session_id).description
            services = []
            if 'services' in environment and 'activeDirectories' in\
                    environment['services']:
                services += environment['services']['activeDirectories']

            if 'services' in environment and 'webServers' in\
                    environment['services']:
                services += environment['services']['webServers']

            service = [service for service in services
                       if service['id'] == service_id][0]

            if service:
                entities = [u['id'] for u in service['units']]
                entities.append(service_id)
                result = []
                for status in statuses:
                    if status.entity_id in entities:
                        result.append(status)

        return {'reports': [status.to_dict() for status in result]}

    def deploy(self, request, environment_id, session_id):
        log.debug(_('Session:Deploy <EnvId: {0}, '
                    'SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        msg = _('Could not deploy session. Session is already '
                'deployed or in deployment state')
        if session.state != 'open':
            log.warn(msg)

        session.state = 'deploying'
        session.save(unit)

        #Set X-Auth-Token for conductor
        env = session.description
        env['token'] = request.context.auth_token

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


def create_resource():
    return wsgi.Resource(Controller())
