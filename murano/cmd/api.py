#!/usr/bin/env python
#
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
import sys

import eventlet

if os.name == 'nt':
    # eventlet monkey patching causes subprocess.Popen to fail on Windows
    # when using pipes due to missing non blocking I/O support
    eventlet.monkey_patch(os=False)
else:
    eventlet.monkey_patch()

# If ../murano/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
root = os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, os.pardir)
if os.path.exists(os.path.join(root, 'murano', '__init__.py')):
    sys.path.insert(0, root)

from murano.api.v1 import request_statistics
from murano.common import config
from murano.common import policy
from murano.common import server
from murano.common import statservice as stats
from murano.common import wsgi
from murano.openstack.common import log
from murano.openstack.common import service


def main():
    try:
        config.parse_args()
        log.setup('murano')
        request_statistics.init_stats()
        policy.init()

        launcher = service.ServiceLauncher()

        app = config.load_paste_app('murano')
        port, host = (config.CONF.bind_port, config.CONF.bind_host)

        launcher.launch_service(wsgi.Service(app, port, host))
        launcher.launch_service(server.get_rpc_service())
        launcher.launch_service(server.get_notification_service())
        launcher.launch_service(stats.StatsCollectingService())

        launcher.wait()
    except RuntimeError as e:
        sys.stderr.write("ERROR: %s\n" % e)
        sys.exit(1)


if __name__ == '__main__':
    main()
