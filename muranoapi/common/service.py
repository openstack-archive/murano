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

import socket

from amqplib.client_0_8 import AMQPConnectionException
import anyjson
import eventlet
from muranoapi.common.utils import retry, handle
from muranoapi.db.models import Status, Session, Environment, Deployment
from muranoapi.db.session import get_session
from muranoapi.openstack.common import log as logging, timeutils
from muranoapi.common import config
from sqlalchemy import desc

amqp = eventlet.patcher.import_patched('amqplib.client_0_8')
conf = config.CONF.reports
rabbitmq = config.CONF.rabbitmq
log = logging.getLogger(__name__)


class TaskResultHandlerService():
    thread = None

    def start(self):
        self.thread = eventlet.spawn(self.connect)

    def stop(self):
        pass

    def wait(self):
        self.thread.wait()

    @retry((socket.error, AMQPConnectionException), tries=-1)
    def connect(self):
        connection = amqp.Connection('{0}:{1}'.
                                     format(rabbitmq.host, rabbitmq.port),
                                     virtual_host=rabbitmq.virtual_host,
                                     userid=rabbitmq.login,
                                     password=rabbitmq.password,
                                     ssl=rabbitmq.use_ssl, insist=True)
        ch = connection.channel()

        def bind(exchange, queue):
            if not exchange:
                ch.exchange_declare(exchange, 'direct', durable=True,
                                    auto_delete=False)
            ch.queue_declare(queue, durable=True, auto_delete=False)
            if not exchange:
                ch.queue_bind(queue, exchange, queue)

        bind(conf.results_exchange, conf.results_queue)
        bind(conf.reports_exchange, conf.reports_queue)

        ch.basic_consume(conf.results_exchange, callback=handle_result)
        ch.basic_consume(conf.reports_exchange, callback=handle_report,
                         no_ack=True)
        while ch.callbacks:
            ch.wait()


@handle
def handle_result(msg):
    log.debug(_('Got result message from '
                'orchestration engine:\n{0}'.format(msg.body)))

    environment_result = anyjson.deserialize(msg.body)
    if 'deleted' in environment_result:
        log.debug(_('Result for environment {0} is dropped. Environment '
                    'is deleted'.format(environment_result['id'])))

        msg.channel.basic_ack(msg.delivery_tag)
        return

    session = get_session()
    environment = session.query(Environment).get(environment_result['id'])

    if not environment:
        log.warning(_('Environment result could not be handled, specified '
                      'environment does not found in database'))
        return

    environment.description = environment_result
    environment.version += 1
    environment.save(session)

    #close session
    conf_session = session.query(Session).filter_by(
        **{'environment_id': environment.id, 'state': 'deploying'}).first()
    conf_session.state = 'deployed'
    conf_session.save(session)

    #close deployment
    deployment = get_last_deployment(session, environment.id)
    deployment.finished = timeutils.utcnow()
    status = Status()
    status.deployment_id = deployment.id
    status.text = "Deployment finished"
    deployment.statuses.append(status)
    deployment.save(session)
    msg.channel.basic_ack(msg.delivery_tag)


@handle
def handle_report(msg):
    log.debug(_('Got report message from orchestration '
                'engine:\n{0}'.format(msg.body)))

    params = anyjson.deserialize(msg.body)
    params['entity_id'] = params['id']
    del params['id']

    status = Status()
    status.update(params)

    session = get_session()
    #connect with deployment
    with session.begin():
        running_deployment = get_last_deployment(session,
                                                 status.environment_id)
        status.deployment_id = running_deployment.id
        session.add(status)


def get_last_deployment(session, env_id):
    query = session.query(Deployment). \
        filter_by(environment_id=env_id). \
        order_by(desc(Deployment.started))
    return query.first()
