#    Copyright (c) 2016 NEC Corporation. All rights reserved.
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

import mock

from oslo_concurrency import processutils
from oslo_log import log as logging

from murano.cmd import engine
from murano.common import config
from murano.tests.unit import base


class TestEngineWorkers(base.MuranoTestCase):

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch('oslo_service.service.launch')
    def test_workers_default(self, launch, setup, parse_args):
        engine.main()
        launch.assert_called_once_with(mock.ANY, mock.ANY,
                                       workers=processutils.get_worker_count(),
                                       restart_method='mutate')

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch('oslo_service.service.launch')
    def test_workers_good_setting(self, launch, setup, parse_args):
        self.override_config("engine_workers", 8, "engine")
        engine.main()
        launch.assert_called_once_with(mock.ANY, mock.ANY, workers=8,
                                       restart_method='mutate')

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch('oslo_service.service.launch')
    def test_workers_zero_setting(self, launch, setup, parse_args):
        self.override_config("engine_workers", 0, "engine")
        engine.main()
        launch.assert_called_once_with(mock.ANY, mock.ANY,
                                       workers=processutils.get_worker_count(),
                                       restart_method='mutate')
