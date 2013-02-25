# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
import traceback

import puka

import logging
import sys

LOG = logging.getLogger(__name__)

class Agent(object):

    def __init__(self, conf):
        self._conf = conf

    def execute(self, command):
        try:
            client = puka.Client("amqp://keero:keero@%s/%s" % (
                self._conf.rabbitmq.host, self._conf.rabbitmq.vhost))
            promise = client.connect()
            client.wait(promise)


            promise = client.queue_declare(queue=command.data['queueName'], durable=True)
            client.wait(promise)

            promise = client.queue_declare(queue=command.data['resultQueueName'], durable=True)
            client.wait(promise)

            promise = client.basic_publish(exchange='', routing_key=command.data['queueName'],
                                           body=command.data['body'])
            client.wait(promise)

            consume_promise = client.basic_consume(queue=command.data['resultQueueName'])
            result = client.wait(consume_promise)

            result_msg = result['body']
            client.basic_ack(result)
            client.basic_cancel(consume_promise)

            promise = client.close()
            client.wait(promise)

            return result_msg
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print exc_type, exc_value, exc_traceback
            print traceback.format_exc()
