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
import sys

import fixtures
import mock
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils
import six
import testtools

from murano.cmd import test_runner
from murano import version

CONF = cfg.CONF
logging.register_options(CONF)
logging.setup(CONF, 'murano')


class TestCaseShell(testtools.TestCase):
    def setUp(self):
        super(TestCaseShell, self).setUp()
        self.auth_params = {'username': 'test',
                            'password': 'test',
                            'project_name': 'test',
                            'auth_url': 'http://localhost:5000'}
        self.args = ['test-runner.py']
        for k, v in six.iteritems(self.auth_params):
            k = '--os-' + k.replace('_', '-')
            self.args.extend([k, v])

        sys.stdout = six.StringIO()
        sys.stderr = six.StringIO()

        self.useFixture(fixtures.MonkeyPatch('keystoneclient.v3.client.Client',
                                             mock.MagicMock))
        dirs = [os.path.dirname(__file__),
                os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                             os.pardir, os.pardir, os.pardir, 'meta')]
        self.override_config('load_packages_from', dirs, 'engine')

    def tearDown(self):
        super(TestCaseShell, self).tearDown()
        CONF.clear()

    def override_config(self, name, override, group=None):
        CONF.set_override(name, override, group, enforce_type=True)
        self.addCleanup(CONF.clear_override, name, group)

    def shell(self, cmd_args=None, exitcode=0):
        orig = sys.stdout
        orig_stderr = sys.stderr
        sys.stdout = six.StringIO()
        sys.stderr = six.StringIO()
        args = self.args
        if cmd_args:
            cmd_args = cmd_args.split()
            args.extend(cmd_args)
        with mock.patch.object(sys, 'argv', args):
            result = self.assertRaises(SystemExit, test_runner.main)
            self.assertEqual(result.code, exitcode,
                             'Command finished with error.')
        stdout = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = orig
        stderr = sys.stderr.getvalue()
        sys.stderr.close()
        sys.stderr = orig_stderr
        return (stdout, stderr)

    def test_help(self):
        stdout, _ = self.shell('--help')
        usage = """usage: murano-test-runner [-h] [--config-file CONFIG_FILE]
                          [--os-auth-url OS_AUTH_URL]
                          [--os-username OS_USERNAME]
                          [--os-password OS_PASSWORD]
                          [--os-project-name OS_PROJECT_NAME]
                          [-l [</path1, /path2> [</path1, /path2> ...]]] [-v]
                          [--version]
                          <PACKAGE_FQN>
                          [<testMethod1, className.testMethod2> [<testMethod1, className.testMethod2"""  # noqa
        self.assertIn(usage, stdout)

    def test_version(self):
        _, stderr = self.shell('--version')
        self.assertIn(version.version_string, stderr)

    @mock.patch.object(test_runner, 'LOG')
    def test_increase_verbosity(self, mock_log):
        self.shell('io.murano.test.MyTest1 -v')
        mock_log.logger.setLevel.assert_called_with(logging.DEBUG)

    @mock.patch('keystoneclient.v3.client.Client')
    def test_os_params_replaces_config(self, mock_client):
        # Load keystone configuration parameters from config
        importutils.import_module('keystonemiddleware.auth_token')
        self.override_config('admin_user', 'new_value', 'keystone_authtoken')

        self.shell('io.murano.test.MyTest1 io.murano.test.MyTest2')

        mock_client.assert_has_calls([mock.call(**self.auth_params)])

    def test_package_all_tests(self):
        _, stderr = self.shell('io.murano.test.MyTest1 -v')
        # NOTE(efedorova): May be, there is a problem with test-runner, since
        # all logs are passed to stderr
        self.assertIn('io.murano.test.MyTest1.testSimple1.....OK', stderr)
        self.assertIn('io.murano.test.MyTest1.testSimple2.....OK', stderr)
        self.assertIn('io.murano.test.MyTest2.testSimple1.....OK', stderr)
        self.assertIn('io.murano.test.MyTest2.testSimple2.....OK', stderr)
        self.assertNotIn('thisIsNotAtestMethod', stderr)

    def test_package_by_class(self):
        _, stderr = self.shell(
            'io.murano.test.MyTest1 io.murano.test.MyTest2 -v')

        self.assertNotIn('io.murano.test.MyTest1.testSimple1.....OK', stderr)
        self.assertNotIn('io.murano.test.MyTest1.testSimple2.....OK', stderr)
        self.assertIn('io.murano.test.MyTest2.testSimple1.....OK', stderr)
        self.assertIn('io.murano.test.MyTest2.testSimple2.....OK', stderr)

    def test_package_by_test_name(self):
        _, stderr = self.shell(
            'io.murano.test.MyTest1 testSimple1 -v')

        self.assertIn('io.murano.test.MyTest1.testSimple1.....OK', stderr)
        self.assertNotIn('io.murano.test.MyTest1.testSimple2.....OK', stderr)
        self.assertIn('io.murano.test.MyTest2.testSimple1.....OK', stderr)
        self.assertNotIn('io.murano.test.MyTest2.testSimple2.....OK', stderr)

    def test_package_by_test_and_class_name(self):
        _, stderr = self.shell(
            'io.murano.test.MyTest1 io.murano.test.MyTest2.testSimple1 -v')

        self.assertNotIn('io.murano.test.MyTest1.testSimple1.....OK', stderr)
        self.assertNotIn('io.murano.test.MyTest1.testSimple2.....OK', stderr)
        self.assertIn('io.murano.test.MyTest2.testSimple1.....OK', stderr)
        self.assertNotIn('io.murano.test.MyTest2.testSimple2.....OK', stderr)

    def test_service_methods(self):
        _, stderr = self.shell(
            'io.murano.test.MyTest1 io.murano.test.MyTest1.testSimple1 -v')
        self.assertIn('Executing: io.murano.test.MyTest1.setUp', stderr)
        self.assertIn('Executing: io.murano.test.MyTest1.tearDown', stderr)

    def test_package_is_not_provided(self):
        _, stderr = self.shell(exitcode=2)
        self.assertIn('murano-test-runner: error: too few arguments', stderr)

    def test_wrong_parent(self):
        _, stderr = self.shell(
            'io.murano.test.MyTest1 io.murano.test.MyTest3 -v', exitcode=1)
        self.assertIn('Class io.murano.test.MyTest3 is not inherited from'
                      ' io.murano.test.TestFixture. Skipping it.', stderr)
        self.assertIn('No tests found for execution.', stderr)
