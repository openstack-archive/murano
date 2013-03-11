import uuid
import pika
from pika.adapters import TornadoConnection
import time

try:
    import tornado.ioloop

    IOLoop = tornado.ioloop.IOLoop
except ImportError:
    IOLoop = None


class RabbitMqClient(object):
    def __init__(self, host='localhost', login='guest',
                 password='guest', virtual_host='/'):
        credentials = pika.PlainCredentials(login, password)
        self._connection_parameters = pika.ConnectionParameters(
            credentials=credentials, host=host, virtual_host=virtual_host)
        self._subscriptions = {}

    def _create_connection(self):
        self.connection = TornadoConnection(
            parameters=self._connection_parameters,
            on_open_callback=self._on_connected)

    def _on_connected(self, connection):
        self._channel = connection.channel(self._on_channel_open)

    def _on_channel_open(self, channel):
        self._channel = channel
        if self._started_callback:
            self._started_callback()

    def _on_queue_declared(self, frame, queue, callback, ctag):
        def invoke_callback(ch, method_frame, header_frame, body):
            callback(body=body,
                     message_id=header_frame.message_id or "")

        self._channel.basic_consume(invoke_callback, queue=queue,
                                    no_ack=True, consumer_tag=ctag)

    def subscribe(self, queue, callback):
        ctag = str(uuid.uuid4())
        self._subscriptions[queue] = ctag

        self._channel.queue_declare(
            queue=queue, durable=True,
            callback=lambda frame, ctag=ctag: self._on_queue_declared(
                frame, queue, callback, ctag))

    def unsubscribe(self, queue):
        self._channel.basic_cancel(consumer_tag=self._subscriptions[queue])
        del self._subscriptions[queue]

    def start(self, callback=None):
        if IOLoop is None: raise ImportError("Tornado not installed")
        self._started_callback = callback
        ioloop = IOLoop.instance()
        self.timeout_id = ioloop.add_timeout(time.time() + 0.1,
                                             self._create_connection)

    def send(self, queue, data, exchange="", message_id=""):
        properties = pika.BasicProperties(message_id=message_id)
        self._channel.queue_declare(
            queue=queue, durable=True,
            callback=lambda frame: self._channel.basic_publish(
                exchange=exchange, routing_key=queue,
                body=data, properties=properties))



