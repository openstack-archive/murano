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

import datetime as dt
import mock
import time

from oslo_utils import timeutils

from murano.common import statservice
from murano.db import models
from murano.db import session as db_session
from murano.services import states
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
        self.assertEqual(2, len(self.service.tg.threads))
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
            "Failed to get statistics object from a "
            "database. {error_code}".format(error_code='test_error_code'))


class EnvReportingTest(base.MuranoNotifyWithDBTestCase):

    def setUp(self):
        super(EnvReportingTest, self).setUp()
        self.service = statservice.StatsCollectingService()

    @mock.patch('murano.common.statservice.status_reporter.'
                'Notification.report')
    def test_report_env_stats(self, mock_notifier):
        now = timeutils.utcnow()
        later = now + dt.timedelta(minutes=1)

        session = db_session.get_session()

        environment1 = models.Environment(
            name='test_environment1', tenant_id='test_tenant_id1',
            version=2, id='test_env_id_1',
            created=now,
            updated=later,
            description={
                'Objects': {
                    'applications': ['app1'],
                    'services': ['service1']
                }
            }
        )
        environment2 = models.Environment(
            name='test_environment2', tenant_id='test_tenant_id2',
            version=1, id='test_env_id_2',
            created=now,
            updated=later,
            description={
                'Objects': {
                    'applications': ['app2'],
                    'services': ['service3']
                }
            }
        )
        environment3 = models.Environment(
            name='test_environment3', tenant_id='test_tenant_id2',
            version=1, id='test_env_id_3',
            created=now,
            updated=later,
            description={}
        )

        session_1 = models.Session(
            environment=environment1, user_id='test_user_id',
            description={},
            state=states.SessionState.DEPLOYED,
            version=1
        )

        session_2 = models.Session(
            environment=environment2, user_id='test_user_id',
            description={},
            state=states.SessionState.DEPLOYED,
            version=0
        )

        session_3 = models.Session(
            environment=environment3, user_id='test_user_id',
            description={},
            state=states.SessionState.DEPLOY_FAILURE,
            version=1
        )

        task_1 = models.Task(
            id='task_id_1',
            environment=environment1,
            description={},
            created=now,
            started=now,
            updated=later,
            finished=later
        )

        task_2 = models.Task(
            id='task_id_2',
            environment=environment2,
            description={},
            created=now,
            started=now,
            updated=later,
            finished=later
        )

        task_3 = models.Task(
            id='task_id_3',
            environment=environment3,
            description={},
            created=now,
            started=now,
            updated=later,
            finished=later
        )

        status_1 = models.Status(
            id='status_id_1',
            task_id='task_id_1',
            text='Deployed',
            level='info'
        )

        status_2 = models.Status(
            id='status_id_2',
            task_id='task_id_2',
            text='Deployed',
            level='info'
        )

        status_3 = models.Status(
            id='status_id_3',
            task_id='task_id_3',
            text='Something was wrong',
            level='error'
        )

        session.add_all([environment1, environment2, environment3])
        session.add_all([session_1, session_2, session_3])
        session.add_all([task_1, task_2, task_3])
        session.add_all([status_1, status_2, status_3])

        session.flush()

        self.service.report_env_stats()

        self.assertEqual(mock_notifier.call_count, 2)

        dict_env_1 = {'version': 2,
                      'updated': later,
                      'tenant_id': u'test_tenant_id1',
                      'created': now,
                      'description_text': u'',
                      'status': 'ready',
                      'id': u'test_env_id_1',
                      'name': u'test_environment1'}

        dict_env_2 = {'version': 1,
                      'updated': later,
                      'tenant_id': u'test_tenant_id2',
                      'created': now,
                      'description_text': u'',
                      'status': 'ready',
                      'id': u'test_env_id_2',
                      'name': u'test_environment2'}

        calls = [mock.call('environment.exists', dict_env_1),
                 mock.call('environment.exists', dict_env_2)]

        mock_notifier.assert_has_calls(calls)
