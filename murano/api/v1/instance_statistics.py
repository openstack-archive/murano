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

from oslo_log import log as logging

from murano.api.v1 import request_statistics
from murano.common import policy
from murano.common import wsgi
from murano.db.services import instances


LOG = logging.getLogger(__name__)
API_NAME = 'EnvironmentStatistics'


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'GetAggregated')
    def get_aggregated(self, request, environment_id):
        LOG.debug('EnvironmentStatistics:GetAggregated')
        target = {"environment_id": environment_id}
        policy.check("get_aggregated_statistics", request.context, target)

        # TODO(stanlagun): Check that caller is authorized to access
        #  tenant's statistics

        return instances.InstanceStatsServices.get_aggregated_stats(
            environment_id)

    @request_statistics.stats_count(API_NAME, 'GetForInstance')
    def get_for_instance(self, request, environment_id, instance_id):
        LOG.debug('EnvironmentStatistics:GetForInstance')
        target = {"environment_id": environment_id, "instance_id": instance_id}
        policy.check("get_instance_statistics", request.context, target)

        # TODO(stanlagun): Check that caller is authorized to access
        #  tenant's statistics

        return instances.InstanceStatsServices.get_raw_environment_stats(
            environment_id, instance_id)

    @request_statistics.stats_count(API_NAME, 'GetForEnvironment')
    def get_for_environment(self, request, environment_id):
        LOG.debug('EnvironmentStatistics:GetForEnvironment')
        target = {"environment_id": environment_id}
        policy.check("get_statistics", request.context, target)

        # TODO(stanlagun): Check that caller is authorized to access
        #  tenant's statistics

        return instances.InstanceStatsServices.get_raw_environment_stats(
            environment_id)


def create_resource():
    return wsgi.Resource(Controller())
