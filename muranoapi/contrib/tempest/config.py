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

import os

from oslo.config import cfg


murano_group = cfg.OptGroup(name='murano', title='murano')

MuranoGroup = [
    cfg.StrOpt('murano_url',
               default='http://127.0.0.1:8082',
               help="murano url"),
    cfg.StrOpt('metadata_url',
               default='http://127.0.0.1:8084',
               help="murano metadata repository url"),
    cfg.StrOpt('agListnerIP',
               default='10.0.0.155',
               help="agListnerIP"),
    cfg.StrOpt('clusterIP',
               default='10.0.0.150',
               help="clusterIP"),
    cfg.BoolOpt('service_available',
                default='True',
                help='mistral available')
]


def register_config(config, config_group, config_opts):
    config.register_group(config_group)
    config.register_opts(config_opts, config_group)

path = os.path.join("%s/config.conf" % os.getcwd())

if os.path.exists(path):
    cfg.CONF([], project='muranointegration', default_config_files=[path])

register_config(cfg.CONF, murano_group, MuranoGroup)

mistral = cfg.CONF.murano
