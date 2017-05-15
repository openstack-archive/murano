#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import mock
import os

from oslo_config import cfg
from paste import deploy

from murano.common import app_loader
from murano.common import config  # noqa
from murano.tests.unit import base

CONF = cfg.CONF


class AppLoaderTest(base.MuranoTestCase):
    def setUp(self):
        super(AppLoaderTest, self).setUp()
        self.override_config('flavor', 'myflavor', 'paste_deploy')
        self.override_config('config_file', 'path/to/myapp-paste.ini',
                             'paste_deploy')
        CONF.config_file = ['myapp.conf']
        CONF.prog = 'myapp'
        CONF.find_file = mock.MagicMock(return_value='path/to/myapp-paste.ini')

    @mock.patch.object(deploy, 'loadapp', return_value=mock.sentinel.myapp)
    def _test_load_paste_app(self, mock_loadapp,
                             appname='myapp',
                             fullname='myapp-myflavor',
                             path='path/to/myapp-paste.ini'):
        expected_config_path = 'config:%s/%s' % (os.path.abspath('.'), path,)

        app = app_loader.load_paste_app(appname)

        mock_loadapp.assert_called_with(expected_config_path, name=fullname)
        self.assertEqual(mock.sentinel.myapp, app)

    def test_load_paste_app(self):
        self._test_load_paste_app()

    def test_load_paste_app_no_name(self):
        self._test_load_paste_app(appname=None)

    def test_load_paste_app_no_flavor(self):
        self.override_config('flavor', None, 'paste_deploy')
        self._test_load_paste_app(fullname='myapp')

    def test_load_paste_app_no_pastedep_cfg_opt(self):
        self.override_config('config_file', None, 'paste_deploy')

        self._test_load_paste_app()

    def test_load_paste_app_no_pastedep_cfg_opt_and_cfg_opt(self):
        self.override_config('config_file', None, 'paste_deploy')
        CONF.config_file = []

        self._test_load_paste_app()
        CONF.find_file.assert_called_with('myapp-paste.ini')

    def test_load_paste_app_no_cfg_at_all(self):
        self.override_config('config_file', None, 'paste_deploy')
        CONF.find_file.return_value = None

        self.assertRaises(RuntimeError, app_loader.load_paste_app, 'myapp')

    def test_load_paste_app_deploy_error(self):
        deploy.loadapp = mock.MagicMock()
        deploy.loadapp.side_effect = LookupError('Oops')

        self.assertRaises(RuntimeError, app_loader.load_paste_app, 'myapp')
