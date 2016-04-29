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


from oslo_config import cfg
import oslo_messaging as messaging
from oslo_utils import timeutils
import six

from murano.common import uuidutils
from murano.dsl import dsl

CONF = cfg.CONF


@dsl.name('io.murano.system.StatusReporter')
class StatusReporter(object):
    transport = None

    def __init__(self, environment):
        if StatusReporter.transport is None:
            StatusReporter.transport = messaging.get_transport(CONF)
        self._notifier = messaging.Notifier(
            StatusReporter.transport,
            publisher_id=uuidutils.generate_uuid(),
            topic='murano')
        if isinstance(environment, six.string_types):
            self._environment_id = environment
        else:
            self._environment_id = environment.id

    def _report(self, instance, msg, details=None, level='info'):
        body = {
            'id': (self._environment_id if instance is None
                   else instance.id),
            'text': msg,
            'details': details,
            'level': level,
            'environment_id': self._environment_id,
            'timestamp': timeutils.isotime(subsecond=True)
        }
        self._notifier.info({}, 'murano.report_notification', body)

    def report(self, instance, msg):
        self._report(instance, msg)

    def report_error_(self, instance, msg):
        self._report(instance, msg, None, 'error')

    @dsl.name('report_error')
    def report_error(self, instance, msg):
        self._report(instance, msg, None, 'error')
