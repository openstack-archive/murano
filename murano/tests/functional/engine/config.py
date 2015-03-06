# Copyright (c) 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from oslo.config import cfg


murano_group = cfg.OptGroup(name='murano', title="murano")

MuranoGroup = [
    cfg.StrOpt('auth_url',
               default='http://127.0.0.1:5000/v2.0/',
               help="keystone url"),
    cfg.StrOpt('user',
               default='admin',
               help="keystone user"),
    cfg.StrOpt('password',
               default='pass',
               help="password for keystone user"),
    cfg.StrOpt('tenant',
               default='admin',
               help='keystone tenant'),
    cfg.StrOpt('murano_url',
               default='http://127.0.0.1:8082/v1/',
               help="murano url"),
    cfg.StrOpt('standard_flavor',
               default='m1.medium',
               help="flavor for sanity tests"),
    cfg.StrOpt('advanced_flavor',
               default='m1.large',
               help="flavor for advanced tests"),
    cfg.StrOpt('linux_image',
               default='default_linux',
               help="image for linux services"),
    cfg.StrOpt('windows_image',
               default='default_windows',
               help="image for windows services")
]


def register_config(config, config_group, config_opts):

    config.register_group(config_group)
    config.register_opts(config_opts, config_group)


def load_config():
    __location = os.path.realpath(os.path.join(os.getcwd(),
                                  os.path.dirname(__file__)))
    path = os.path.join(__location, "config.conf")

    if os.path.exists(path):
        cfg.CONF([], project='muranointegration', default_config_files=[path])

    register_config(cfg.CONF, murano_group, MuranoGroup)
