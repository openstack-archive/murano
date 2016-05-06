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


def create_rmq_client():
    rabbitmq = CONF.rabbitmq
    connection_params = {
        'login': rabbitmq.login,
        'password': rabbitmq.password,
        'host': rabbitmq.host,
        'port': rabbitmq.port,
        'virtual_host': rabbitmq.virtual_host,
        'ssl': rabbitmq.ssl,
        'ca_certs': rabbitmq.ca_certs.strip() or None,
        'insecure': rabbitmq.insecure
    }
    return mqclient.MqClient(**connection_params)
