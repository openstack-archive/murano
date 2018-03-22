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

import mock
import sys

from oslo_concurrency import processutils
from oslo_log import log as logging

from murano.cmd import api
from murano.common import app_loader
from murano.common import config
from murano.common import policy
from murano.tests.unit import base


class TestAPIWorkers(base.MuranoTestCase):

    def setUp(self):
        super(TestAPIWorkers, self).setUp()
        sys.argv = ['murano']

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch.object(policy, 'init')
    @mock.patch.object(config, 'set_middleware_defaults')
    @mock.patch.object(app_loader, 'load_paste_app')
    @mock.patch('oslo_service.service.launch')
    def test_workers_default(self, launch, setup, parse_args, init,
                             load_paste_app, set_middleware_defaults):
        api.main()
        launch.assert_called_once_with(mock.ANY, mock.ANY,
                                       workers=processutils.get_worker_count(),
                                       restart_method='mutate')

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch.object(policy, 'init')
    @mock.patch.object(config, 'set_middleware_defaults')
    @mock.patch.object(app_loader, 'load_paste_app')
    @mock.patch('oslo_service.service.launch')
    def test_workers_good_setting(self, launch, setup, parse_args, init,
                                  load_paste_app, set_middleware_defaults):
        self.override_config("api_workers", 8, "murano")
        api.main()
        launch.assert_called_once_with(mock.ANY, mock.ANY, workers=8,
                                       restart_method='mutate')

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch.object(policy, 'init')
    @mock.patch.object(config, 'set_middleware_defaults')
    @mock.patch.object(app_loader, 'load_paste_app')
    @mock.patch('oslo_service.service.launch')
    def test_workers_zero_setting(self, launch, setup, parse_args, init,
                                  load_paste_app, set_middleware_defaults):
        self.override_config("api_workers", 0, "murano")
        api.main()
        launch.assert_called_once_with(mock.ANY, mock.ANY,
                                       workers=processutils.get_worker_count(),
                                       restart_method='mutate')
