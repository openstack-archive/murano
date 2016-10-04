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
import time

from murano.common.i18n import _LE
from murano.common import statservice
from murano.tests.unit import base


@mock.patch('murano.common.statservice.v1.stats',
            request_count=11, error_count=22, average_time=33,
            requests_per_tenant=44)
class StatsCollectingServiceTest(base.MuranoTestCase):

    def setUp(self):
        super(StatsCollectingServiceTest, self).setUp()
        self.service = statservice.StatsCollectingService()
        self.service._prev_time = 0
        self.mock_new_stats = mock.MagicMock(request_count=1, error_count=2)
        self.service._stats_db = mock.MagicMock(
            get_stats_by_host=mock.MagicMock(return_value=self.mock_new_stats))
        statservice.LOG = mock.MagicMock()

    def test_service_start_and_stop(self, _):
        self.assertEqual(0, len(self.service.tg.threads))
        self.service.start()
        self.assertEqual(1, len(self.service.tg.threads))
        self.service.stop()
        self.assertEqual(0, len(self.service.tg.threads))

    @mock.patch('murano.common.statservice.time')
    def test_update_stats(self, mock_time, mock_stats):
        now = time.time()
        mock_time.time.return_value = now

        self.service.update_stats()

        statservice.LOG.debug.assert_any_call(
            'Stats: (Requests: 11  Errors: 22  Ave.Res.Time 33.0000\n Per '
            'tenant: 44)')
        self.assertEqual(now, self.service._prev_time)
        self.assertEqual(mock_stats.request_count,
                         self.mock_new_stats.request_count)
        self.assertEqual(mock_stats.error_count,
                         self.mock_new_stats.error_count)
        self.assertEqual(mock_stats.average_time,
                         self.mock_new_stats.average_response_time)
        self.assertEqual(str(mock_stats.requests_per_tenant),
                         self.mock_new_stats.requests_per_tenant)
        self.assertEqual((11 - 1) / now,
                         self.mock_new_stats.requests_per_second)
        self.assertEqual((22 - 2) / now,
                         self.mock_new_stats.errors_per_second)
        self.service._stats_db.update.assert_called_once_with(
            self.service._hostname, self.mock_new_stats)

    @mock.patch('murano.common.statservice.multiprocessing.cpu_count',
                return_value=5)
    @mock.patch('murano.common.statservice.psutil.cpu_percent',
                return_value=12.3)
    def test_update_stats_with_create_stats_db(self, _, __, mock_stats):
        self.service._stats_db.get_stats_by_host.return_value = None

        result = self.service.update_stats()

        self.assertIsNone(result)
        self.service._stats_db.create.assert_called_once_with(
            self.service._hostname, mock_stats.request_count,
            mock_stats.error_count, mock_stats.average_time,
            mock_stats.requests_per_tenant, 5, 12.3
        )

    @mock.patch('murano.common.statservice.LOG')
    def test_update_stats_handle_exception(self, mock_log, _):
        self.service._stats_db.update.side_effect =\
            Exception('test_error_code')

        self.service.update_stats()

        mock_log.exception.assert_called_once_with(
            _LE("Failed to get statistics object from a "
                "database. {error_code}").format(error_code='test_error_code'))
