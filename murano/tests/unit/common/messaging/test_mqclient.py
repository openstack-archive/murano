# Copyright 2016 AT&T Corp
# All Rights Reserved.
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

import mock
from oslo_serialization import jsonutils
import ssl as ssl_module

from murano.common.messaging import mqclient
from murano.tests.unit import base


class MQClientTest(base.MuranoTestCase):

    @mock.patch('murano.common.messaging.mqclient.kombu')
    def setUp(self, mock_kombu):
        super(MQClientTest, self).setUp()
        self.ssl_client = mqclient.MqClient(login='test_login',
                                            password='test_password',
                                            host='test_host', port='test_port',
                                            virtual_host='test_virtual_host',
                                            ssl=True, ca_certs=['cert1'],
                                            insecure=False)

        mock_kombu.Connection.assert_called_once_with(
            'amqp://{0}:{1}@{2}:{3}/{4}'.format('test_login', 'test_password',
                                                'test_host', 'test_port',
                                                'test_virtual_host'),
            ssl={'ca_certs': ['cert1'], 'cert_reqs': ssl_module.CERT_REQUIRED})
        self.assertEqual(mock_kombu.Connection(), self.ssl_client._connection)
        self.assertIsNone(self.ssl_client._channel)
        self.assertFalse(self.ssl_client._connected)

    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_alternate_client_initializations(self, mock_kombu):
        for ca_cert in ['cert1', None]:
            client = mqclient.MqClient(login='test_login',
                                       password='test_password',
                                       host='test_host', port='test_port',
                                       virtual_host='test_virtual_host',
                                       ssl=True,
                                       ca_certs=ca_cert,
                                       insecure=True)

            mock_kombu.Connection.assert_called_once_with(
                'amqp://{0}:{1}@{2}:{3}/{4}'.format('test_login',
                                                    'test_password',
                                                    'test_host', 'test_port',
                                                    'test_virtual_host'),
                ssl={'ca_certs': ca_cert,
                     'cert_reqs': ssl_module.CERT_OPTIONAL
                     if ca_cert else ssl_module.CERT_NONE})
            self.assertEqual(mock_kombu.Connection(),
                             client._connection)
            mock_kombu.Connection.reset_mock()

        client = mqclient.MqClient(login='test_login',
                                   password='test_password',
                                   host='test_host', port='test_port',
                                   virtual_host='test_virtual_host',
                                   ssl=False,
                                   ca_certs=None,
                                   insecure=False)

        mock_kombu.Connection.assert_called_once_with(
            'amqp://{0}:{1}@{2}:{3}/{4}'.format('test_login',
                                                'test_password',
                                                'test_host', 'test_port',
                                                'test_virtual_host'),
            ssl=None)
        self.assertEqual(mock_kombu.Connection(),
                         client._connection)

    def test_connect(self):
        self.ssl_client.connect()

        self.ssl_client._connection.connect.assert_called_once_with()
        self.ssl_client._connection.channel.assert_called_once_with()
        self.assertEqual(self.ssl_client._connection.channel(),
                         self.ssl_client._channel)
        self.assertTrue(self.ssl_client._connected)

    def test_close(self):
        self.ssl_client.close()

        self.ssl_client._connection.close.assert_called_once_with()
        self.assertFalse(self.ssl_client._connected)

    def test_enter_and_exit(self):
        with self.ssl_client:
            pass

        self.ssl_client._connection.connect.assert_called_once_with()
        self.ssl_client._connection.close.assert_called_once_with()

    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_declare(self, mock_kombu):
        self.ssl_client.connect()
        self.ssl_client.declare(queue='test_queue', exchange='test_exchange',
                                enable_ha=True, ttl=1)

        queue_args = {
            'x-ha-policy': 'all',
            'x-expires': 1
        }
        mock_kombu.Exchange.assert_called_once_with(
            'test_exchange', type='direct', durable=True)
        mock_kombu.Queue.assert_called_once_with('test_queue',
                                                 mock_kombu.Exchange(),
                                                 'test_queue',
                                                 durable=True,
                                                 queue_arguments=queue_args)
        mock_kombu.Queue()().declare.assert_called_once_with()
        mock_kombu.reset_mock()

        self.ssl_client.declare(queue='test_queue', exchange='test_exchange',
                                enable_ha=False, ttl=0)

        mock_kombu.Exchange.assert_called_once_with(
            'test_exchange', type='direct', durable=True)
        mock_kombu.Queue.assert_called_once_with('test_queue',
                                                 mock_kombu.Exchange(),
                                                 'test_queue',
                                                 durable=True,
                                                 queue_arguments={})

    def test_declare_except_runtime_error(self):
        with self.assertRaisesRegexp(RuntimeError,
                                     'Not connected to RabbitMQ'):
            self.ssl_client.declare(None)

    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_send(self, mock_kombu):
        mock_message = mock.MagicMock(body='test_message', id=3)

        self.ssl_client.connect()
        self.ssl_client.send(mock_message, 'test_key', 'test_exchange')

        mock_kombu.Producer.assert_called_once_with(
            self.ssl_client._connection)
        mock_kombu.Producer().publish.assert_called_once_with(
            exchange='test_exchange', routing_key='test_key',
            body=jsonutils.dumps('test_message'), message_id='3')

    def test_send_except_runtime_error(self):
        with self.assertRaisesRegexp(RuntimeError,
                                     'Not connected to RabbitMQ'):
            self.ssl_client.send(None, None)

    @mock.patch('murano.common.messaging.mqclient.subscription')
    def test_open(self, mock_subscription):
        self.ssl_client.connect()
        self.ssl_client.open('test_queue', prefetch_count=2)
        mock_subscription.Subscription.assert_called_once_with(
            self.ssl_client._connection, 'test_queue', 2)

    def test_open_except_runtime_error(self):
        with self.assertRaisesRegexp(RuntimeError,
                                     'Not connected to RabbitMQ'):
            self.ssl_client.open(None)
