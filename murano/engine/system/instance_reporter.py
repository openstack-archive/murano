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

from oslo_config import cfg
import oslo_messaging as messaging

from murano.common import uuidutils
from murano.dsl import dsl

CONF = cfg.CONF

UNCLASSIFIED = 0
APPLICATION = 100
OS_INSTANCE = 200


@dsl.name('io.murano.system.InstanceNotifier')
class InstanceReportNotifier(object):
    transport = None

    def __init__(self, environment):
        if InstanceReportNotifier.transport is None:
            InstanceReportNotifier.transport = \
                messaging.get_notification_transport(CONF)
        self._notifier = messaging.Notifier(
            InstanceReportNotifier.transport,
            publisher_id=uuidutils.generate_uuid(),
            topics=['murano'])
        self._environment_id = environment.id

    def _track_instance(self, instance, instance_type,
                        type_title, unit_count):
        payload = {
            'instance': instance.id,
            'environment': self._environment_id,
            'instance_type': instance_type,
            'type_name': instance.type.name,
            'type_title': type_title,
            'unit_count': unit_count
        }

        self._notifier.info({}, 'murano.track_instance', payload)

    def _untrack_instance(self, instance, instance_type):
        payload = {
            'instance': instance.id,
            'environment': self._environment_id,
            'instance_type': instance_type,
        }

        self._notifier.info({}, 'murano.untrack_instance', payload)

    def track_application(self, instance, title=None, unit_count=None):
        self._track_instance(instance, APPLICATION, title, unit_count)

    def untrack_application(self, instance):
        self._untrack_instance(instance, APPLICATION)

    def track_cloud_instance(self, instance):
        self._track_instance(instance, OS_INSTANCE, None, 1)

    def untrack_cloud_instance(self, instance):
        self._untrack_instance(instance, OS_INSTANCE)
