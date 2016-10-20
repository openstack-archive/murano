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

from murano.db import models
from murano.db.services import stats as statistics
from murano.db import session as db_session
from murano.tests.unit import base


class TestStats(base.MuranoWithDBTestCase):

    def setUp(self):
        super(TestStats, self).setUp()

        self.stats_list = []
        self.stats_kwargs = {
            'host': 'test_host',
            'request_count': 5,
            'error_count': 2,
            'average_response_time': 0.5,
            'requests_per_tenant': 1,
            'cpu_count': 4,
            'cpu_percent': 0.3
        }
        self.stats_kwargs_2 = {
            'host': 'test_host_2',
            'request_count': 6,
            'error_count': 3,
            'average_response_time': 0.6,
            'requests_per_tenant': 2,
            'cpu_count': 5,
            'cpu_percent': 0.4
        }

    def tearDown(self):
        super(TestStats, self).tearDown()

        unit = db_session.get_session()
        for stat in self.stats_list:
            with unit.begin():
                unit.delete(stat)

    def _create_stats(self, which_kwargs):
        stats = models.ApiStats()
        for key, val in which_kwargs.items():
            setattr(stats, key, val)
        stats.requests_per_second = 1.2
        stats.errors_per_second = 2.3

        unit = db_session.get_session()
        with unit.begin():
            unit.add(stats)

        self.assertIsNotNone(stats)
        self.stats_list.append(stats)

        return stats

    def _are_stats_equal(self, x, y, check_type=False):
        comparison_attributes = ['host', 'request_count', 'error_count',
                                 'average_response_time',
                                 'requests_per_tenant',
                                 'requests_per_second',
                                 'errors_per_second',
                                 'cpu_count', 'cpu_percent']
        if check_type:
            if type(x) != type(y):
                return False
        for attr in comparison_attributes:
            try:
                if str(getattr(x, attr)) != str(getattr(y, attr)):
                    return False
            except AttributeError:
                if str(x[attr]) != str(getattr(y, attr)):
                    return False
        return True

    def test_create(self):
        statistics.Statistics.create(**self.stats_kwargs)

        unit = db_session.get_session()
        retrieved_stats = None
        with unit.begin():
            retrieved_stats = unit.query(models.ApiStats)\
                .order_by(models.ApiStats.id.desc()).first()

        self.stats_kwargs['requests_per_second'] = 0.0
        self.stats_kwargs['errors_per_second'] = 0.0
        self.assertIsNotNone(retrieved_stats)
        self.assertTrue(
            self._are_stats_equal(self.stats_kwargs, retrieved_stats))

    def test_update(self):
        """Note: this test expects to test update functionality.

        However, the current implementation of Statistics.update() does not
        actually update the host of the statistics object passed in.
        It just saves the object that is passed in, which appears to contradict
        its intended use case.
        """
        stats = models.ApiStats()
        for key, val in self.stats_kwargs.items():
            setattr(stats, key, val)
        statistics.Statistics.update('test_host', stats)

        unit = db_session.get_session()
        retrieved_stats = None
        with unit.begin():
            retrieved_stats = unit.query(models.ApiStats)\
                .order_by(models.ApiStats.id.desc()).first()
        self.assertIsNotNone(retrieved_stats)
        self.assertTrue(
            self._are_stats_equal(stats, retrieved_stats, check_type=True))

    def test_get_stats_by_id(self):
        stats = self._create_stats(self.stats_kwargs)
        retrieved_stats = statistics.Statistics.get_stats_by_id(stats.id)
        self.assertIsNotNone(retrieved_stats)
        self.assertTrue(
            self._are_stats_equal(stats, retrieved_stats, check_type=True))

    def test_get_stats_by_host(self):
        stats = self._create_stats(self.stats_kwargs)
        retrieved_stats = statistics.Statistics.get_stats_by_host(stats.host)
        self.assertIsNotNone(retrieved_stats)
        self.assertTrue(
            self._are_stats_equal(stats, retrieved_stats, check_type=True))

    def test_get_all(self):
        stats = self._create_stats(self.stats_kwargs)
        retrieved_stats = statistics.Statistics.get_all()
        self.assertIsInstance(retrieved_stats, list)
        self.assertEqual(1, len(retrieved_stats))
        self.assertTrue(
            self._are_stats_equal(stats, retrieved_stats[0], check_type=True))

        stats = self._create_stats(self.stats_kwargs_2)
        retrieved_stats = statistics.Statistics.get_all()
        self.assertIsInstance(retrieved_stats, list)
        self.assertEqual(2, len(retrieved_stats))
        self.assertTrue(
            self._are_stats_equal(stats, retrieved_stats[1], check_type=True))
