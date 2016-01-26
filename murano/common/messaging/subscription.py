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

import collections
import socket
import time

from eventlet import patcher

from murano.common.messaging import message

kombu = patcher.import_patched('kombu')


class Subscription(object):
    def __init__(self, connection, queue, prefetch_count=1):
        self._buffer = collections.deque()
        self._connection = connection
        self._queue = kombu.Queue(name=queue, exchange=None)
        self._consumer = kombu.Consumer(self._connection, auto_declare=False)
        self._consumer.register_callback(self._receive)
        self._consumer.qos(prefetch_count=prefetch_count)

    def __enter__(self):
        self._consumer.add_queue(self._queue)
        self._consumer.consume()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._consumer is not None:
            self._consumer.cancel()
        return False

    def get_message(self, timeout=None):
        msg_handle = self._get(timeout=timeout)
        if msg_handle is None:
            return None
        return message.Message(self._connection, msg_handle)

    def _get(self, timeout=None):
        elapsed = 0.0
        remaining = timeout
        while True:
            time_start = time.time()
            if self._buffer:
                return self._buffer.pop()
            try:
                self._connection.drain_events(timeout=timeout and remaining)
            except socket.timeout:
                return None
            elapsed += time.time() - time_start
            remaining = timeout and timeout - elapsed or None

    def _receive(self, message_data, message):
        self._buffer.append(message)
