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

from datetime import datetime
import socket

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import six

from murano.common import uuidutils
from murano.dsl import dsl

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


@dsl.name('io.murano.system.StatusReporter')
class StatusReporter(object):
    transport = None

    def __init__(self, environment):
        if StatusReporter.transport is None:
            StatusReporter.transport = messaging.get_notification_transport(
                CONF)
        self._notifier = messaging.Notifier(
            StatusReporter.transport,
            publisher_id=uuidutils.generate_uuid(),
            topics=['murano'])
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
            'timestamp': datetime.utcnow().isoformat()
        }
        self._notifier.info({}, 'murano.report_notification', body)

    def report(self, instance, msg):
        self._report(instance, msg)

    def report_error_(self, instance, msg):
        self._report(instance, msg, None, 'error')

    @dsl.name('report_error')
    def report_error(self, instance, msg):
        self._report(instance, msg, None, 'error')


class Notification(object):
    transport = None

    def __init__(self):
        if not CONF.stats.env_audit_enabled:
            return

        if Notification.transport is None:
            Notification.transport = messaging.get_notification_transport(CONF)
        self._notifier = messaging.Notifier(
            Notification.transport,
            publisher_id=('murano.%s' % socket.gethostname()),
            driver='messaging')

    def _report(self, event_type, environment, level='info'):
        if not CONF.stats.env_audit_enabled:
            return

        if 'deleted' in environment:
            deleted_at = environment['deleted'].isoformat()
        else:
            deleted_at = None

        body = {
            'id': environment['id'],
            'level': level,
            'environment_id': environment['id'],
            'tenant_id': environment['tenant_id'],
            'created_at': environment.get('created').isoformat(),
            'deleted_at': deleted_at,
            'launched_at': None,
            'timestamp': datetime.utcnow().isoformat()
        }

        optional_fields = ("deployment_started", "deployment_finished")
        for f in optional_fields:
            body[f] = environment.get(f, None)

        LOG.debug("Sending out notification, type=%s, body=%s, level=%s",
                  event_type, body, level)

        self._notifier.info({}, 'murano.%s' % event_type,
                            body)

    def report(self, event_type, environment):
        self._report(event_type, environment)

    def report_error(self, event_type, environment):
        self._report(event_type, environment, 'error')


NOTIFIER = None


def get_notifier():
    global NOTIFIER
    if not NOTIFIER:
        NOTIFIER = Notification()

    return NOTIFIER
