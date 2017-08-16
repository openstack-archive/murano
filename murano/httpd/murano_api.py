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

"""WSGI script for murano-api.

Script for running murano-api under Apache2.
"""


from oslo_config import cfg
import oslo_i18n as i18n
from oslo_log import log as logging

from murano.api.v1 import request_statistics
from murano.common import app_loader
from murano.common import config
from murano.common.i18n import _
from murano.common import policy
from murano.common import server


def init_application():
    i18n.enable_lazy()

    LOG = logging.getLogger('murano.api')

    logging.register_options(cfg.CONF)
    cfg.CONF(project='murano')
    logging.setup(cfg.CONF, 'murano')
    config.set_middleware_defaults()
    request_statistics.init_stats()
    policy.init()
    server.get_notification_listener().start()
    server.get_rpc_server().start()

    port = cfg.CONF.bind_port
    host = cfg.CONF.bind_host
    LOG.info(_('Starting Murano REST API on %(host)s:%(port)s'),
             {'host': host, 'port': port})
    return app_loader.load_paste_app('murano')
