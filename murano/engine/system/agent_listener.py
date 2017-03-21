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

import greenlet
from oslo_config import cfg
from oslo_log import log as logging

from murano.common import exceptions
from murano.dsl import dsl
from murano.engine.system import common

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class AgentListenerException(Exception):
    pass


@dsl.name('io.murano.system.AgentListener')
class AgentListener(object):
    def __init__(self, name):
        self._enabled = not CONF.engine.disable_murano_agent
        self._results_queue = str('-execution-results-%s' % name.lower())
        self._subscriptions = {}
        self._receive_thread = None

    def _check_enabled(self):
        if CONF.engine.disable_murano_agent:
            LOG.error('Use of murano-agent is disallowed '
                      'by the server configuration')

            raise exceptions.PolicyViolationException(
                'Use of murano-agent is disallowed '
                'by the server configuration')

    @property
    def enabled(self):
        return self._enabled

    def queue_name(self):
        return self._results_queue

    def start(self):
        if CONF.engine.disable_murano_agent:
            # Noop
            LOG.debug("murano-agent is disabled by the server")
            return

        if self._receive_thread is None:
            dsl.get_execution_session().on_session_finish(
                lambda: self.stop())
            self._receive_thread = dsl.spawn(
                self._receive,
                dsl.get_this().find_owner('io.murano.CloudRegion'))

    def stop(self):
        if CONF.engine.disable_murano_agent:
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

    def subscribe(self, message_id, event):
        self._check_enabled()
        self._subscriptions[message_id] = event
        self.start()

    def unsubscribe(self, message_id):
        self._check_enabled()
        self._subscriptions.pop(message_id)

    def _receive(self, region):
        with common.create_rmq_client(region) as client:
            client.declare(self._results_queue, enable_ha=True, ttl=86400000)
            with client.open(self._results_queue) as subscription:
                while True:
                    msg = subscription.get_message()
                    if not msg:
                        continue
                    msg.ack()
                    msg_id = msg.body.get('SourceID', msg.id)
                    LOG.debug("Got execution result: id '{msg_id}'"
                              " body '{body}'".format(msg_id=msg_id,
                                                      body=msg.body))
                    if msg_id in self._subscriptions:
                        event = self._subscriptions.pop(msg_id)
                        event.send(msg.body)
