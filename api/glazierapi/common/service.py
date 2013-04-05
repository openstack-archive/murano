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

import anyjson
from eventlet import patcher
from glazierapi.db.models import Status, Session, Environment
from glazierapi.db.session import get_session

amqp = patcher.import_patched('amqplib.client_0_8')

from glazierapi.openstack.common import service
from glazierapi.openstack.common import log as logging
from glazierapi.common import config

conf = config.CONF.reports
rabbitmq = config.CONF.rabbitmq
log = logging.getLogger(__name__)
channel = None


class TaskResultHandlerService(service.Service):
    def __init__(self, threads=1000):
        super(TaskResultHandlerService, self).__init__(threads)

    def start(self):
        super(TaskResultHandlerService, self).start()
        self.tg.add_thread(self._handle_results)

    def stop(self):
        super(TaskResultHandlerService, self).stop()

    def _handle_results(self):
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


def handle_report(msg):
    log.debug(_('Got report message from orchestration engine:\n{0}'.
                format(msg.body)))

    params = anyjson.deserialize(msg.body)
    params['entity_id'] = params['id']
    del params['id']

    status = Status()
    status.update(params)

    session = get_session()
    #connect with session
    conf_session = session.query(Session).filter_by(
        **{'environment_id': status.environment_id,
           'state': 'deploying'}).first()
    status.session_id = conf_session.id

    with session.begin():
        session.add(status)


def handle_result(msg):
    log.debug(_('Got result message from '
                'orchestration engine:\n{0}'.format(msg.body)))

    environment_result = anyjson.deserialize(msg.body)
    if 'deleted' in environment_result:
        log.debug(_('Result for environment {0} is dropped. '
                    'Environment is deleted'.format(environment_result['id'])))

        msg.channel.basic_ack(msg.delivery_tag)
        return

    session = get_session()
    environment = session.query(Environment).get(environment_result['id'])

    environment.description = environment_result
    environment.save(session)

    #close session
    conf_session = session.query(Session).filter_by(
        **{'environment_id': environment.id, 'state': 'deploying'}).first()
    conf_session.state = 'deployed'
    conf_session.save(session)

    msg.channel.basic_ack(msg.delivery_tag)
