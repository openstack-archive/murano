# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ssl as ssl_module

from eventlet import patcher
from oslo_serialization import jsonutils
from oslo_service import sslutils

from murano.common.i18n import _
from murano.common.messaging import subscription

kombu = patcher.import_patched('kombu')


class MqClient(object):
    def __init__(self, login, password, host, port, virtual_host,
                 ssl=False, ssl_version=None, ca_certs=None, insecure=False):
        ssl_params = None

        if ssl:
            cert_reqs = ssl_module.CERT_REQUIRED
            if insecure:
                if ca_certs:
                    cert_reqs = ssl_module.CERT_OPTIONAL
                else:
                    cert_reqs = ssl_module.CERT_NONE

            ssl_params = {
                'ca_certs': ca_certs,
                'cert_reqs': cert_reqs
            }

            if ssl_version:
                key = ssl_version.lower()
                try:
                    ssl_params['ssl_version'] = sslutils._SSL_PROTOCOLS[key]
                except KeyError:
                    raise RuntimeError(
                        _("Invalid SSL version: %s") % ssl_version)

        self._connection = kombu.Connection(
            'amqp://{0}:{1}@{2}:{3}/{4}'.format(
                login,
                password,
                host,
                port,
                virtual_host
            ), ssl=ssl_params
        )
        self._channel = None
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def connect(self):
        self._connection.connect()
        self._channel = self._connection.channel()
        self._connected = True

    def close(self):
        self._connection.close()
        self._connected = False

    def declare(self, queue, exchange='', enable_ha=False, ttl=0):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        queue_arguments = {}
        if enable_ha is True:
            # To use mirrored queues feature in RabbitMQ 2.x
            # we need to declare this policy on the queue itself.
            #
            # Warning: this option has no effect on RabbitMQ 3.X,
            # to enable mirrored queues feature in RabbitMQ 3.X, please
            # configure RabbitMQ.
            queue_arguments['x-ha-policy'] = 'all'
        if ttl > 0:
            queue_arguments['x-expires'] = ttl

        exchange = kombu.Exchange(exchange, type='direct', durable=True)
        queue = kombu.Queue(queue, exchange, queue, durable=True,
                            queue_arguments=queue_arguments)
        bound_queue = queue(self._connection)
        bound_queue.declare()

    def send(self, message, key, exchange='', signing_func=None):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        producer = kombu.Producer(self._connection)
        data = jsonutils.dumps(message.body)
        headers = None
        if signing_func:
            headers = {'signature':  signing_func(data)}

        producer.publish(
            exchange=str(exchange),
            routing_key=str(key),
            body=data,
            message_id=str(message.id),
            headers=headers
        )

    def open(self, queue, prefetch_count=1):
        if not self._connected:
            raise RuntimeError('Not connected to RabbitMQ')

        return subscription.Subscription(
            self._connection, queue, prefetch_count)
