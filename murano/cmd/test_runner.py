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

import argparse
import os
import re
import sys
import traceback

import eventlet
from keystoneclient.v3 import client as ks_client
from muranoclient.common import exceptions as exc
from muranoclient.common import utils
from oslo_config import cfg
from oslo_db import options
from oslo_log import log as logging
from oslo_utils import importutils
import six

from murano import version
from murano.common.i18n import _, _LE
from murano.common import config
from murano.common import engine
from murano.dsl import exceptions
from murano.dsl import executor
from murano.dsl import helpers
from murano.engine import execution_session
from murano.engine import mock_context_manager
from murano.engine import package_loader


CONF = cfg.CONF
LOG = logging.getLogger(__name__)
options.set_defaults(CONF)

BASE_CLASS = 'io.murano.test.TestFixture'
TEST_CASE_NAME = re.compile('^test(?![a-z])')

if os.name == 'nt':
    # eventlet monkey patching causes subprocess.Popen to fail on Windows
    # when using pipes due to missing non blocking I/O support
    eventlet.monkey_patch(os=False)
else:
    eventlet.monkey_patch()


class MuranoTestRunner(object):
    def __init__(self):
        self.parser = self.get_parser()
        self.args = self.parser.parse_args()

        if self.args.verbose:
            LOG.logger.setLevel(logging.DEBUG)

    def _load_package(self, pkg_loader, name):
        try:
            parts = name.rsplit('/')
            if len(parts) == 2:
                name, pkg_version = parts
                version_spec = helpers.parse_version_spec(pkg_version)
            else:
                version_spec = helpers.parse_version_spec('*')
            package = pkg_loader.load_package(name, version_spec)
        except exceptions.NoPackageFound:
            if not CONF.engine.load_packages_from:
                msg = _('Local package is not found since "load-packages-from"'
                        ' engine parameter is not provided and specified '
                        'packages is not loaded to murano-api')
            else:
                msg = _('Specified package is not found: {0} were scanned '
                        'together with murano database'
                        ).format(','.join(
                            CONF.engine.load_packages_from))
            LOG.error(msg)
            self.error(msg, show_help=False)
        except exc.CommunicationError:
            msg = ('Murano API is not running. '
                   'Check configuration parameters.')
            LOG.error(msg)
            self.error(msg, show_help=False)
        return package

    def _get_methods_to_run(self, package, tests_to_run, class_to_methods):
        if not tests_to_run:
            return class_to_methods

        methods_to_run = {}

        for item in tests_to_run:
            # Check for method name occurrence in all methods.
            # if there is no dot in provided item - it is a method name
            if '.' not in item:
                for class_name, methods in six.iteritems(class_to_methods):
                    methods_to_run[class_name] = []
                    if item in methods:
                        methods_to_run[class_name].append(item)
                continue
            # Check match for the whole class name
            if item in package.classes:
                # Add all test cases from specified package
                if item in class_to_methods:
                    methods_to_run[item] = class_to_methods[item]
                continue

            # Check match for the class together with method specified
            class_to_test, test_method = item.rsplit('.', 1)
            if class_to_test in package.classes:
                methods_to_run[class_to_test] = [
                    m for m in class_to_methods[class_to_test]
                    if m == test_method]
                continue
        methods_count = sum(len(v) for v in six.itervalues(methods_to_run))
        methods = [k + '.' + method
                   for k, v in six.iteritems(methods_to_run) for method in v]
        LOG.debug('{0} method(s) is(are) going to be executed: '
                  '\n{1}'.format(methods_count, '\n'.join(methods)))
        return methods_to_run

    def _get_test_cases_by_classes(self, package):
        """Build valid test cases list for each class in the provided package.

           Check, if test class and test case name are valid.
           Return class mappings to test cases.
        """
        class_to_methods = {}
        for pkg_class_name in package.classes:
            class_obj = package.find_class(pkg_class_name, False)
            base_class = package.find_class(BASE_CLASS)
            if not base_class.is_compatible(class_obj):
                LOG.debug('Class {0} is not inherited from {1}. '
                          'Skipping it.'.format(pkg_class_name, BASE_CLASS))
                continue

            # Exclude methods, that are not test cases.
            tests = []
            valid_test_name = TEST_CASE_NAME

            for m in class_obj.methods:
                if valid_test_name.match(m):
                    tests.append(m)
            class_to_methods[pkg_class_name] = tests
        return class_to_methods

    def _call_service_method(self, name, exc, obj):
        if name in obj.type.methods:
            obj.type.methods[name].usage = 'Action'
            LOG.debug('Executing: {0}.{1}'.format(obj.type.name, name))
            obj.type.invoke(name, exc, obj, (), {})

    def _validate_keystone_opts(self, args):
        ks_opts_to_config = {
            'auth_url': 'auth_uri',
            'username': 'admin_user',
            'password': 'admin_password',
            'project_name': 'admin_tenant_name'}

        ks_opts = {'auth_url': getattr(args, 'os_auth_url', None),
                   'username': getattr(args, 'os_username', None),
                   'password': getattr(args, 'os_password', None),
                   'project_name': getattr(args, 'os_project_name', None)}

        if None in ks_opts.values() and not CONF.default_config_files:
            msg = _LE('Please provide murano config file or credentials for '
                      'authorization: {0}').format(
                ', '.join(['--os-auth-url', '--os-username', '--os-password',
                           '--os-project-name', '--os-tenant-id']))
            LOG.error(msg)
            self.error(msg)
        # Load keystone configuration parameters from config
        importutils.import_module('keystonemiddleware.auth_token')

        for param, value in six.iteritems(ks_opts):
            if not value:
                ks_opts[param] = getattr(CONF.keystone_authtoken,
                                         ks_opts_to_config[param])
            if param == 'auth_url':
                ks_opts[param] = ks_opts[param].replace('v2.0', 'v3')
        return ks_opts

    def error(self, msg, show_help=True):
        sys.stderr.write("ERROR: {msg}\n\n".format(msg=msg))
        if show_help:
            self.parser.print_help()
        sys.exit(1)

    def run_tests(self):
        exit_code = 0
        provided_pkg_name = self.args.package
        load_packages_from = self.args.load_packages_from
        tests_to_run = self.args.tests

        ks_opts = self._validate_keystone_opts(self.args)

        client = ks_client.Client(**ks_opts)
        test_session = execution_session.ExecutionSession()
        test_session.token = client.auth_token
        test_session.project_id = client.project_id

        # Replace location of loading packages with provided from command line.
        if load_packages_from:
            cfg.CONF.engine.load_packages_from = load_packages_from
        with package_loader.CombinedPackageLoader(test_session) as pkg_loader:
            engine.get_plugin_loader().register_in_loader(pkg_loader)

            package = self._load_package(pkg_loader, provided_pkg_name)
            class_to_methods = self._get_test_cases_by_classes(package)
            run_set = self._get_methods_to_run(package,
                                               tests_to_run,
                                               class_to_methods)
            if run_set:
                LOG.debug('Starting test execution.')
            else:
                msg = _('No tests found for execution.')
                LOG.error(msg)
                self.error(msg)

            for pkg_class, test_cases in six.iteritems(run_set):
                for m in test_cases:
                    # Create new executor for each test case to provide
                    # pure test environment
                    dsl_executor = executor.MuranoDslExecutor(
                        pkg_loader,
                        mock_context_manager.MockContextManager(),
                        test_session)
                    obj = package.find_class(pkg_class, False).new(
                        None, dsl_executor.object_store, dsl_executor)(None)
                    self._call_service_method('setUp', dsl_executor, obj)
                    obj.type.methods[m].usage = 'Action'

                    test_session.start()
                    try:
                        obj.type.invoke(m, dsl_executor, obj, (), {})
                        LOG.debug('\n.....{0}.{1}.....OK'.format(obj.type.name,
                                                                 m))
                        self._call_service_method(
                            'tearDown', dsl_executor, obj)
                    except Exception:
                        LOG.exception('\n.....{0}.{1}.....FAILURE\n'
                                      ''.format(obj.type.name, m))
                        exit_code = 1
                    finally:
                        test_session.finish()
        return exit_code

    def get_parser(self):
        parser = argparse.ArgumentParser(prog='murano-test-runner')
        parser.set_defaults(func=self.run_tests)
        parser.add_argument('--config-file',
                            help='Path to the murano config')

        parser.add_argument('--os-auth-url',
                            default=utils.env('OS_AUTH_URL'),
                            help='Defaults to env[OS_AUTH_URL]')
        parser.add_argument('--os-username',
                            default=utils.env('OS_USERNAME'),
                            help='Defaults to env[OS_USERNAME]')

        parser.add_argument('--os-password',
                            default=utils.env('OS_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD]')

        parser.add_argument('--os-project-name',
                            default=utils.env('OS_PROJECT_NAME'),
                            help='Defaults to env[OS_PROJECT_NAME]')
        parser.add_argument('-l', '--load_packages_from',
                            nargs='*', metavar='</path1, /path2>',
                            help='Directory to search packages from. '
                                 'We be added to the list of current directory'
                                 ' list, provided in a config file.')
        parser.add_argument("-v", "--verbose", action="store_true",
                            help="increase output verbosity")
        parser.add_argument('--version', action='version',
                            version=version.version_string)
        parser.add_argument('package',
                            metavar='<PACKAGE_FQN>',
                            help='Full name of application package that is '
                                 'going to be tested')
        parser.add_argument('tests', nargs='*',
                            metavar='<testMethod1, className.testMethod2>',
                            help='List of method names to be tested')
        return parser


def main():
    test_runner = MuranoTestRunner()
    try:
        if test_runner.args.config_file:
            default_config_files = [test_runner.args.config_file]
        else:
            default_config_files = cfg.find_config_files('murano')
            if not default_config_files:
                murano_conf = os.path.join(os.path.dirname(__file__),
                                           os.pardir,
                                           os.pardir,
                                           'etc', 'murano',
                                           'murano.conf')
                if os.path.exists(murano_conf):
                    default_config_files = [murano_conf]
        sys.argv = [sys.argv[0]]
        config.parse_args(default_config_files=default_config_files)
        logging.setup(CONF, 'murano')
    except RuntimeError as e:
        LOG.exception(_LE("Failed to initialize murano-test-runner: %s") % e)
        sys.exit("ERROR: %s" % e)

    try:
        exit_code = test_runner.run_tests()
        sys.exit(exit_code)
    except Exception as e:
        tb = traceback.format_exc()
        err_msg = _LE("Command failed: {0}\n{1}").format(e, tb)
        LOG.error(err_msg)
        sys.exit(err_msg)


if __name__ == '__main__':
    main()
