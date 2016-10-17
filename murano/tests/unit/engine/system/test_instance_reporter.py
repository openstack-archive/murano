#    Copyright (c) 2016 AT&T
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

from murano.db import models
from murano.engine.system import instance_reporter
from murano.tests.unit import base

LATEST_VERSION = 1


class TestInstanceReporter(base.MuranoTestCase):
    def setUp(self):
        super(TestInstanceReporter, self).setUp()

        self.environment = models.Environment(
            name='test_environment', tenant_id='test_tenant_id',
            version=LATEST_VERSION
        )

        self.addCleanup(mock.patch.stopall)

    @mock.patch("murano.db.models")
    def test_track_untrack_application(self, mock_models):
        instance = mock_models.Instance()
        self.i_r = instance_reporter.InstanceReportNotifier(self.environment)
        self.assertEqual(self.environment.id, self.i_r._environment_id)
        self.assertIsNone(self.i_r.track_application(instance))
        self.assertIsNone(self.i_r.untrack_application(instance))

    @mock.patch("murano.db.models")
    def test_track_untrack_cloud_instance(self, mock_models):
        instance = mock_models.Instance()
        self.i_r = instance_reporter.InstanceReportNotifier(self.environment)
        self.assertEqual(self.environment.id, self.i_r._environment_id)
        self.assertIsNone(self.i_r.track_cloud_instance(instance))
        self.assertIsNone(self.i_r.untrack_cloud_instance(instance))
