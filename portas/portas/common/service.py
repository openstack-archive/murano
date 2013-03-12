import anyjson
from eventlet import patcher
from portas.db.models import Status, Session, Environment
from portas.db.session import get_session

amqp = patcher.import_patched('amqplib.client_0_8')

from portas.openstack.common import service
from portas.openstack.common import log as logging
from portas.common import config

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
        connection = amqp.Connection('{0}:{1}'.format(rabbitmq.host, rabbitmq.port), virtual_host=rabbitmq.virtual_host,
                                     userid=rabbitmq.userid, password=rabbitmq.password,
                                     ssl=rabbitmq.use_ssl, insist=True)
        ch = connection.channel()

        def bind(exchange, queue):
            if not exchange:
                ch.exchange_declare(exchange, 'direct', durable=True, auto_delete=False)
            ch.queue_declare(queue, durable=True, auto_delete=False)
            if not exchange:
                ch.queue_bind(queue, exchange, queue)

        bind(conf.results_exchange, conf.results_queue)
        bind(conf.reports_exchange, conf.reports_queue)

        ch.basic_consume(conf.results_exchange, callback=handle_result, no_ack=True)
        ch.basic_consume(conf.reports_exchange, callback=handle_report, no_ack=True)
        while ch.callbacks:
            ch.wait()


def handle_report(msg):
    log.debug(_('Got report message from orchestration engine:\n{0}'.format(msg.body)))

    params = anyjson.deserialize(msg.body)
    params['entity_id'] = params['id']
    del params['id']

    status = Status()
    status.update(params)

    session = get_session()
    #connect with session
    conf_session = session.query(Session).filter_by(
        **{'environment_id': status.environment_id, 'state': 'deploying'}).first()
    status.session_id = conf_session.id

    with session.begin():
        session.add(status)

    msg.channel.basic_ack(msg.delivery_tag)


def handle_result(msg):
    log.debug(_('Got result message from orchestration engine:\n{0}'.format(msg.body)))

    environment_result = anyjson.deserialize(msg.body)

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
