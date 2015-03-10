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

import eventlet
import greenlet

import murano.common.config as config
import murano.common.exceptions as exceptions
from murano.dsl import helpers
import murano.dsl.murano_class as murano_class
import murano.dsl.murano_object as murano_object
import murano.engine.system.common as common
from murano.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class AgentListenerException(Exception):
    pass


@murano_class.classname('io.murano.system.AgentListener')
class AgentListener(murano_object.MuranoObject):
    def initialize(self, _context, name):
        self._enabled = False
        if config.CONF.engine.disable_murano_agent:
            return
        self._enabled = True
        self._results_queue = str('-execution-results-%s' % name.lower())
        self._subscriptions = {}
        self._receive_thread = None

    def _check_enabled(self):
        if config.CONF.engine.disable_murano_agent:
            LOG.debug(
                'Use of murano-agent is disallowed '
                'by the server configuration')

            raise exceptions.PolicyViolationException(
                'Use of murano-agent is disallowed '
                'by the server configuration')

    @property
    def enabled(self):
        return self._enabled

    def queueName(self):
        return self._results_queue

    def start(self, _context):
        if config.CONF.engine.disable_murano_agent:
            # Noop
            LOG.debug("murano-agent is disabled by the server")
            return

        if self._receive_thread is None:
            helpers.get_environment(_context).on_session_finish(
                lambda: self.stop())
            self._receive_thread = eventlet.spawn(self._receive)

    def stop(self):
        if config.CONF.engine.disable_murano_agent:
            # Noop
            LOG.debug("murano-agent is disabled by the server")
            return

        if self._receive_thread is not None:
            self._receive_thread.kill()
            try:
                self._receive_thread.wait()
            except greenlet.GreenletExit:
                pass
            finally:
                self._receive_thread = None

    def subscribe(self, message_id, event, _context):
        self._check_enabled()
        self._subscriptions[message_id] = event
        self.start(_context)

    def unsubscribe(self, message_id):
        self._check_enabled()
        self._subscriptions.pop(message_id)

    def _receive(self):
        with common.create_rmq_client() as client:
            client.declare(self._results_queue, enable_ha=True, ttl=86400000)
            with client.open(self._results_queue) as subscription:
                while True:
                    msg = subscription.get_message()
                    if not msg:
                        continue
                    msg.ack()
                    msg_id = msg.body.get('SourceID', msg.id)
                    LOG.debug("Got execution result: id '{0}'"
                              " body '{1}'".format(msg_id, msg.body))
                    if msg_id in self._subscriptions:
                        event = self._subscriptions.pop(msg_id)
                        event.send(msg.body)
