#    Copyright (c) 2013 Mirantis, Inc.
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

import json

from murano.db import models as m
from murano.db import session as db_session


class Statistics(object):

    @staticmethod
    def get_all():
        db = db_session.get_session()
        stats = db.query(m.ApiStats).all()
        return stats

    @staticmethod
    def get_stats_by_id(stats_id):
        db = db_session.get_session()
        stats = db.query(m.ApiStats).get(stats_id)
        return stats

    @staticmethod
    def get_stats_by_host(host):
        db = db_session.get_session()
        stats = db.query(m.ApiStats).filter(m.ApiStats.host == host).first()
        return stats

    @staticmethod
    def create(host, request_count, error_count,
               average_response_time, requests_per_tenant, cpu_count,
               cpu_percent):
        stats = m.ApiStats()
        stats.host = host
        stats.request_count = request_count
        stats.error_count = error_count
        stats.average_response_time = average_response_time
        stats.requests_per_tenant = json.dumps(requests_per_tenant)
        stats.requests_per_second = 0.0
        stats.errors_per_second = 0.0
        stats.cpu_count = cpu_count
        stats.cpu_percent = cpu_percent

        db = db_session.get_session()
        stats.save(db)

    @staticmethod
    def update(host, stats):
        db = db_session.get_session()
        stats.save(db)
