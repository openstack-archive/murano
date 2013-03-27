from eventlet import patcher
puka = patcher.import_patched('puka')
#import puka
import anyjson
import config


class RmqClient(object):
    def __init__(self):
        settings = config.CONF.rabbitmq
        self._client = puka.Client('amqp://{0}:{1}@{2}:{3}/{4}'.format(
            settings.login,
            settings.password,
            settings.host,
            settings.port,
            settings.virtual_host
        ))
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def connect(self):
        if not self._connected:
            promise = self._client.connect()
            self._client.wait(promise, timeout=10000)
            self._connected = True

    def close(self):
        if self._connected:
            self._client.close()
            self._connected = False

    def declare(self, queue, exchange=None):
        promise = self._client.queue_declare(str(queue), durable=True)
        self._client.wait(promise)

        if exchange:
            promise = self._client.exchange_declare(str(exchange), durable=True)
            self._client.wait(promise)
            promise = self._client.queue_bind(
                str(queue), str(exchange), routing_key=str(queue))
            self._client.wait(promise)

    def send(self, message, key, exchange='', timeout=None):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        headers = { 'message_id': message.id }

        promise = self._client.basic_publish(
            exchange=str(exchange),
            routing_key=str(key),
            body=anyjson.dumps(message.body),
            headers=headers)
        self._client.wait(promise, timeout=timeout)

    def open(self, queue):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        return Subscription(self._client, queue)


class Subscription(object):
    def __init__(self, client, queue):
        self._client = client
        self._queue = queue
        self._promise = None
        self._lastMessage = None

    def __enter__(self):
        self._promise = self._client.basic_consume(
            queue=self._queue,
            prefetch_count=1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ack_last()
        promise = self._client.basic_cancel(self._promise)
        self._client.wait(promise)
        return False

    def _ack_last(self):
        if self._lastMessage:
            self._client.basic_ack(self._lastMessage)
            self._lastMessage = None

    def get_message(self, timeout=None):
        if not self._promise:
            raise RuntimeError(
                "Subscription object must be used within 'with' block")
        self._ack_last()
        self._lastMessage = self._client.wait(self._promise, timeout=timeout)
        #print self._lastMessage
        msg = Message()
        msg.body = anyjson.loads(self._lastMessage['body'])
        msg.id = self._lastMessage['headers'].get('message_id')
        return msg


class Message(object):
    def __init__(self):
        self._body = {}
        self._id = ''

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        self._body = value

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value or ''

