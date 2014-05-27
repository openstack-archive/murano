# Copyright (c) 2014 Mirantis Inc.
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

from oslo import messaging

from murano.common import config
from murano.common import uuidutils
from murano.dsl import murano_class
from murano.openstack.common import log as logging


LOG = logging.getLogger(__name__)


@murano_class.classname('io.murano.system.StatusReporter')
class StatusReporter(object):
    transport = None

    def initialize(self, environment):
        if StatusReporter.transport is None:
            StatusReporter.transport = \
                messaging.get_transport(config.CONF)
        self._notifier = messaging.Notifier(
            StatusReporter.transport,
            publisher_id=uuidutils.generate_uuid(),
            topic='murano')
        self._environment_id = environment.object_id

    def _report(self, instance, msg, details=None, level='info'):
        body = {
            'id': instance.object_id,
            'text': msg,
            'details': details,
            'level': level,
            'environment_id': self._environment_id
        }
        self._notifier.info({}, 'murano.report_notification', body)

    def report(self, instance, msg):
        self._report(instance, msg)

    def report_error(self, instance, msg):
        self._report(instance, msg, None, 'error')
