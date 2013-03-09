from eventlet import patcher

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
        connection = amqp.Connection(rabbitmq.host, virtual_host=rabbitmq.virtual_host,
                                     userid=rabbitmq.userid, password=rabbitmq.password,
                                     ssl=rabbitmq.use_ssl, insist=True)
        ch = connection.channel()

        def bind(exchange, queue):
            ch.exchange_declare(exchange, 'direct')
            ch.queue_declare(queue)
            ch.queue_bind(queue, exchange, queue)

        bind(conf.results_exchange, conf.results_queue)
        bind(conf.reports_exchange, conf.reports_queue)

        ch.basic_consume('task-results', callback=handle_result)
        ch.basic_consume('task-reports', callback=handle_report)
        while ch.callbacks:
            ch.wait()


def handle_report(msg):
    msg.channel.basic_ack(msg.delivery_tag)
    log.debug(_('Got report message from orchestration engine:\n{0}'.format(msg.body)))

def handle_result(msg):
    msg.channel.basic_ack(msg.delivery_tag)
    log.debug(_('Got result message from orchestration engine:\n{0}'.format(msg.body)))