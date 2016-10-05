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
from oslo_db import exception
from oslo_utils import timeutils

from murano.db.services import instances
from murano.tests.unit import base as test_base


@mock.patch('murano.db.services.instances.db_session')
class TestInstances(test_base.MuranoTestCase):

    @mock.patch('murano.db.services.instances.timeutils')
    @mock.patch('murano.db.services.instances.models')
    def test_track_instance(self, mock_models, mock_timeutils,
                            mock_db_session):
        mock_env = mock.MagicMock(tenant_id='test_tenant_id')
        mock_db_session.get_session().query().get.return_value = mock_env
        now = timeutils.utcnow_ts()
        mock_timeutils.utcnow_ts.return_value = now

        track_instance = instances.InstanceStatsServices.track_instance
        track_instance('test_instance_id', 'test_env_id', 'test_type',
                       'test_type_name', 'test_type_title', unit_count=1)

        mock_models.Instance.assert_called_once_with()
        self.assertEqual('test_instance_id',
                         mock_models.Instance().instance_id)
        self.assertEqual('test_env_id', mock_models.Instance().environment_id)
        self.assertEqual('test_instance_id',
                         mock_models.Instance().instance_id)
        self.assertEqual('test_tenant_id', mock_models.Instance().tenant_id)
        self.assertEqual('test_type', mock_models.Instance().instance_type)
        self.assertEqual(now, mock_models.Instance().created)
        self.assertIsNone(mock_models.Instance().destroyed)
        self.assertEqual('test_type_name', mock_models.Instance().type_name)
        self.assertEqual('test_type_title', mock_models.Instance().type_title)
        self.assertEqual(1, mock_models.Instance().unit_count)
        mock_db_session.get_session().add.assert_called_once_with(
            mock_models.Instance())

    @mock.patch('murano.db.services.instances.models')
    def test_track_instance_except_duplicate_entry(self, _, mock_db_session):
        mock_db_session.get_session().add.side_effect =\
            exception.DBDuplicateEntry

        track_instance = instances.InstanceStatsServices.track_instance
        track_instance('test_instance_id', 'test_env_id', 'test_type',
                       'test_type_name', 'test_type_title')

        self.assertEqual(1, mock_db_session.get_session().execute.call_count)

    @mock.patch('murano.db.services.instances.timeutils')
    def test_destroy_instance(self, mock_timeutils, mock_db_session):
        mock_instance = mock.MagicMock(destroyed=False)
        mock_db_session.get_session().query().get.return_value = mock_instance
        now = timeutils.utcnow_ts()
        mock_timeutils.utcnow_ts.return_value = now

        destroy_instance = instances.InstanceStatsServices.destroy_instance
        destroy_instance('test_instance_id', 'test_environment_id')

        self.assertEqual(now, mock_instance.destroyed)
        mock_instance.save.assert_called_once_with(
            mock_db_session.get_session())

    def test_get_aggregated_stats(self, mock_db_session):
        mock_db_session.get_session().query().filter().group_by().all\
            .return_value = [['1', '2', '3'], ['4', '5', '6']]

        get_stats = instances.InstanceStatsServices.get_aggregated_stats
        result = get_stats('test_env_id')

        expected_result = [
            {'type': 1, 'duration': 2, 'count': 3},
            {'type': 4, 'duration': 5, 'count': 6},
        ]

        self.assertEqual(expected_result, result)

    @mock.patch('murano.db.services.instances.timeutils')
    def test_get_raw_environment_stats(self, mock_timeutils, mock_db_session):
        now = timeutils.utcnow_ts()
        mock_timeutils.utcnow_ts.return_value = now
        mock_db_session.get_session().query().filter().filter().all.\
            return_value = [
                mock.MagicMock(instance_type='test_instance_type',
                               created=now - 1000,
                               destroyed=now,
                               type_name='test_type_name',
                               unit_count=1,
                               instance_id='test_instance_id',
                               type_title='test_type_title'),
                mock.MagicMock(instance_type='test_instance_type_2',
                               created=now - 2000,
                               destroyed=None,
                               type_name='test_type_name_2',
                               unit_count=2,
                               instance_id='test_instance_id_2',
                               type_title='test_type_title_2')
            ]
        mock_db_session.reset_mock()

        get_env_stats = instances.InstanceStatsServices.\
            get_raw_environment_stats
        result = get_env_stats('test_env_id', 'test_instance_id')

        expected_result = [
            {
                'type': 'test_instance_type',
                'duration': 1000,  # now - (now - 1000) = 1000
                'type_name': 'test_type_name',
                'unit_count': 1,
                'instance_id': 'test_instance_id',
                'type_title': 'test_type_title',
                'active': False
            },
            {
                'type': 'test_instance_type_2',
                'duration': 2000,  # now - (now - 2000) = 2000
                'type_name': 'test_type_name_2',
                'unit_count': 2,
                'instance_id': 'test_instance_id_2',
                'type_title': 'test_type_title_2',
                'active': True
            },
        ]

        self.assertEqual(expected_result, result)
        # Assert that two filters were performed, the second one for
        # the instance_id argument.
        self.assertEqual(1,
                         mock_db_session.get_session().query().filter.
                         call_count)
        self.assertEqual(1,
                         mock_db_session.get_session().query().filter().
                         filter.call_count)
