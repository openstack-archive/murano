# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import fixtures
import logging
import mock
import urllib
import webob

from murano.api.v1 import request_statistics
from murano.common import rpc
from murano.openstack.common import timeutils
from murano.openstack.common import wsgi
from murano.tests import base
from murano.tests import utils

TEST_DEFAULT_LOGLEVELS = {'migrate': logging.WARN, 'sqlalchemy': logging.WARN}


def test_with_middleware(self, middleware, func, req, *args, **kwargs):
    @webob.dec.wsgify
    def _app(req):
        return func(req, *args, **kwargs)

    resp = middleware(_app).process_request(req)
    return resp


class FakeLogMixin:
    """Allow logs to be tested (rather than just disabling
    logging. This is taken from heat
    """
    def setup_logging(self):
        # Assign default logs to self.LOG so we can still
        # assert on heat logs.
        self.LOG = self.useFixture(
            fixtures.FakeLogger(level=logging.DEBUG))
        base_list = set([nlog.split('.')[0]
                         for nlog in logging.Logger.manager.loggerDict])
        for base in base_list:
            if base in TEST_DEFAULT_LOGLEVELS:
                self.useFixture(fixtures.FakeLogger(
                    level=TEST_DEFAULT_LOGLEVELS[base],
                    name=base))
            elif base != 'murano':
                self.useFixture(fixtures.FakeLogger(
                    name=base))


class MuranoApiTestCase(base.MuranoWithDBTestCase, FakeLogMixin):
    # Set this if common.rpc is imported into other scopes so that
    # it can be mocked properly
    RPC_IMPORT = 'murano.common.rpc'

    def setUp(self):
        super(MuranoApiTestCase, self).setUp()

        self.setup_logging()

        # Mock the RPC classes
        self.mock_api_rpc = mock.Mock(rpc.ApiClient)
        self.mock_engine_rpc = mock.Mock(rpc.EngineClient)
        mock.patch(self.RPC_IMPORT + '.engine',
                   return_value=self.mock_engine_rpc).start()
        mock.patch(self.RPC_IMPORT + '.api',
                   return_value=self.mock_api_rpc).start()

        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        super(MuranoApiTestCase, self).tearDown()
        timeutils.utcnow.override_time = None

    def _stub_uuid(self, values=[]):
        class FakeUUID:
            def __init__(self, v):
                self.hex = v

        mock_uuid4 = mock.patch('uuid.uuid4').start()
        mock_uuid4.side_effect = [FakeUUID(v) for v in values]
        return mock_uuid4


class ControllerTest(object):
    """
    Common utilities for testing API Controllers.
    """

    def __init__(self, *args, **kwargs):
        super(ControllerTest, self).__init__(*args, **kwargs)

        #cfg.CONF.set_default('host', 'server.test')
        self.api_version = '1.0'
        self.tenant = 'test_tenant'
        self.mock_policy_check = None

        request_statistics.init_stats()

    def _environ(self, path):
        return {
            'SERVER_NAME': 'server.test',
            'SERVER_PORT': 8082,
            'SCRIPT_NAME': '/v1',
            'PATH_INFO': path,
            'wsgi.url_scheme': 'http',
        }

    def _simple_request(self, path, params=None, method='GET'):
        """Returns a request with a fake but valid-looking context
        and sets the request environment variables. If `params` is given,
        it should be a dictionary or sequence of tuples.
        """
        environ = self._environ(path)
        environ['REQUEST_METHOD'] = method

        if params:
            qs = urllib.urlencode(params)
            environ['QUERY_STRING'] = qs

        req = wsgi.Request(environ)
        req.context = utils.dummy_context('api_test_user', self.tenant)
        self.context = req.context
        return req

    def _get(self, path, params=None):
        return self._simple_request(path, params=params)

    def _delete(self, path):
        return self._simple_request(path, method='DELETE')

    def _data_request(self, path, data, content_type='application/json',
                      method='POST'):
        environ = self._environ(path)
        environ['REQUEST_METHOD'] = method

        req = wsgi.Request(environ)
        req.context = utils.dummy_context('api_test_user', self.tenant)
        self.context = req.context
        req.body = data
        return req

    def _post(self, path, data, content_type='application/json'):
        return self._data_request(path, data, content_type)

    def _put(self, path, data, content_type='application/json'):
        return self._data_request(path, data, content_type, method='PUT')

    def _mock_policy_setup(self, mocker, action, allowed=True,
                           target=None, expected_request_count=1):
        if self.mock_policy_check is not None:
            # Test existing policy check record
            self._check_policy()
            self.mock_policy_check.reset_mock()

        self.mock_policy_check = mocker
        self.policy_action = action
        self.mock_policy_check.return_value = allowed
        self.policy_target = target
        self.expected_request_count = expected_request_count

    def _check_policy(self):
        """Assert policy checks called as expected"""
        if self.mock_policy_check:
            # Check that policy enforcement got called as expected
            self.mock_policy_check.assert_called_with(
                self.policy_action,
                self.context,
                self.policy_target or {})
            self.assertEqual(self.expected_request_count,
                             len(self.mock_policy_check.call_args_list))

    def tearDown(self):
        self._check_policy()
        super(ControllerTest, self).tearDown()
