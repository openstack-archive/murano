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

import eventlet

from muranoapi.common import config
from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging
from muranoapi.openstack.common import service

conf = config.CONF.stats
log = logging.getLogger(__name__)


class StatsCollectingService(service.Service):
    def __init__(self):
        super(StatsCollectingService, self).__init__()

    def start(self):
        super(StatsCollectingService, self).start()
        self.tg.add_thread(self._collect_stats_loop)

    def stop(self):
        self(StatsCollectingService, self).stop()

    def _collect_stats_loop(self):
        period = conf.period * 60
        while True:
            self.update_stats()
            eventlet.sleep(period)

    def update_stats(self):
        log.debug(_("Updating statistic information."))
