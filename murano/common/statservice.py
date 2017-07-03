#    Copyright (c) 2014 Mirantis, Inc.
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
import multiprocessing
import socket
import time

import eventlet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service
import psutil
from sqlalchemy import desc

from murano.api import v1
from murano.api.v1.deployments import set_dep_state
from murano.api.v1 import request_statistics
from murano.db import models
from murano.db.services import environments as envs
from murano.db.services import stats as db_stats
from murano.db import session as db_session
from murano.engine.system import status_reporter

CONF = cfg.CONF

CONF_STATS = CONF.stats
LOG = logging.getLogger(__name__)


class StatsCollectingService(service.Service):
    def __init__(self):
        super(StatsCollectingService, self).__init__()
        request_statistics.init_stats()
        self._hostname = socket.gethostname()
        self._stats_db = db_stats.Statistics()
        self._prev_time = time.time()
        self._notifier = status_reporter.Notification()

    def start(self):
        super(StatsCollectingService, self).start()
        self.tg.add_thread(self._collect_stats_loop)
        self.tg.add_thread(self._report_env_stats_loop)

    def stop(self):
        super(StatsCollectingService, self).stop()

    def _collect_stats_loop(self):
        period = CONF_STATS.period * 60
        while True:
            self.update_stats()
            eventlet.sleep(period)

    def _report_env_stats_loop(self):
        env_audit_period = CONF_STATS.env_audit_period * 60
        while True:
            self.report_env_stats()
            eventlet.sleep(env_audit_period)

    def update_stats(self):
        LOG.debug("Updating statistic information.")
        LOG.debug("Stats object: {stats}".format(stats=v1.stats))
        LOG.debug("Stats: (Requests: {amount}  Errors: {error}  "
                  "Ave.Res.Time {time:2.4f}\n Per tenant: {req_count})".format(
                      amount=v1.stats.request_count,
                      error=v1.stats.error_count,
                      time=v1.stats.average_time,
                      req_count=v1.stats.requests_per_tenant))
        try:
            stats = self._stats_db.get_stats_by_host(self._hostname)
            if stats is None:
                self._stats_db.create(self._hostname,
                                      v1.stats.request_count,
                                      v1.stats.error_count,
                                      v1.stats.average_time,
                                      v1.stats.requests_per_tenant,
                                      multiprocessing.cpu_count(),
                                      psutil.cpu_percent())
                return

            now = time.time()
            t_delta = now - self._prev_time
            requests_per_second = (v1.stats.request_count -
                                   stats.request_count) / t_delta
            errors_per_second = (v1.stats.error_count -
                                 stats.error_count) / t_delta
            self._prev_time = now
            stats.request_count = v1.stats.request_count
            stats.error_count = v1.stats.error_count
            stats.average_response_time = v1.stats.average_time
            stats.requests_per_tenant = json.dumps(v1.stats.
                                                   requests_per_tenant)
            stats.requests_per_second = requests_per_second
            stats.errors_per_second = errors_per_second
            stats.cpu_percent = psutil.cpu_percent()
            self._stats_db.update(self._hostname, stats)
        except Exception as e:
            LOG.exception("Failed to get statistics object from a "
                          "database. {error_code}".format(error_code=e))

    def report_env_stats(self):
        LOG.debug("Reporting env stats")
        try:
            environments = envs.EnvironmentServices.get_environments_by({})

            for env in environments:
                deployments = get_env_deployments(env.id)
                success_deployments = [d for d in deployments
                                       if d['state'] == "success"]
                if success_deployments:
                    self._notifier.report('environment.exists', env.to_dict())
        except Exception:
            LOG.exception("Failed to report existing envs")


def get_env_deployments(environment_id):
    unit = db_session.get_session()
    query = unit.query(models.Task).filter_by(
        environment_id=environment_id).order_by(desc(models.Task.created))
    result = query.all()
    deployments = [
        set_dep_state(deployment, unit).to_dict() for deployment in result]
    return deployments
