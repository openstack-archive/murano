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

from murano.common.messaging import mqclient

CONF = cfg.CONF


def create_rmq_client(environment):
    region_name = environment['region']
    region_configs = environment['regionConfigs']
    region_config = region_configs.get(region_name, region_configs[None])
    rmq_settings = region_config['agentRabbitMq'].copy()
    rmq_settings['ca_certs'] = CONF.rabbitmq.ca_certs.strip() or None
    return mqclient.MqClient(**rmq_settings)
