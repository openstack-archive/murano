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

import logging

import fixtures
import mock
from oslo_utils import timeutils
import routes
from six.moves import urllib
import webob

from murano.api.v1 import request_statistics
from murano.api.v1 import router
from murano.common import policy
from murano.common import rpc
from murano.common import wsgi
from murano.tests.unit import base
from murano.tests.unit import utils

TEST_DEFAULT_LOGLEVELS = {'migrate': logging.WARN, 'sqlalchemy': logging.WARN}


def test_with_middleware(self, middleware, func, req, *args, **kwargs):
    @webob.dec.wsgify
    def _app(req):
        return func(req, *args, **kwargs)

    resp = middleware(_app).process_request(req)
    return resp


class FakeLogMixin(object):
    """Allows logs to be tested

    Allow logs to be tested (rather than just disabling
    logging. This is taken from heat
    """
    def setup_logging(self):
        # Assign default logs to self.LOG so we can still
        # assert on heat logs.
        self.LOG = self.useFixture(
            fixtures.FakeLogger(level=logging.DEBUG))
        base_list = set([nlog.split('.')[0]
                         for nlog in logging.Logger.manager.loggerDict])
        for base_name in base_list:
            if base_name in TEST_DEFAULT_LOGLEVELS:
                self.useFixture(fixtures.FakeLogger(
                    level=TEST_DEFAULT_LOGLEVELS[base_name],
                    name=base_name))
            elif base_name != 'murano':
                self.useFixture(fixtures.FakeLogger(
                    name=base_name))


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
        mock.patch('murano.db.services.environments.EnvironmentServices.'
                   'get_network_driver', return_value='neutron').start()

        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        super(MuranoApiTestCase, self).tearDown()
        timeutils.utcnow.override_time = None

    def _stub_uuid(self, values=None):
        class FakeUUID(object):
            def __init__(self, v):
                self.hex = v

        if values is None:
            values = []
        mock_uuid4 = mock.patch('uuid.uuid4').start()
        mock_uuid4.side_effect = [FakeUUID(v) for v in values]
        return mock_uuid4


class ControllerTest(object):
    """Common utilities for testing API Controllers."""

    DEFAULT_USER = 'test_user'
    DEFAULT_TENANT = 'test_tenant'

    def __init__(self, *args, **kwargs):
        super(ControllerTest, self).__init__(*args, **kwargs)

        # cfg.CONF.set_default('host', 'server.test')
        self.api_version = '1.0'
        self.tenant = 'test_tenant'
        self.user = 'test_user'
        self.mock_policy_check = None
        self.mapper = routes.Mapper()
        self.api = router.API(self.mapper)

        request_statistics.init_stats()

    def setUp(self):
        super(ControllerTest, self).setUp()

        self.is_admin = False

        policy.init(use_conf=False)
        real_policy_check = policy.check

        self._policy_check_expectations = []
        self._actual_policy_checks = []

        def wrap_policy_check(rule, ctxt, target=None, **kwargs):
            if target is None:
                target = {}
            self._actual_policy_checks.append((rule, target))
            return real_policy_check(rule, ctxt, target=target, **kwargs)

        mock.patch('murano.common.policy.check',
                   side_effect=wrap_policy_check).start()

        # Deny everything
        self._set_policy_rules({"default": "!"})

    def _environ(self, path):
        return {
            'SERVER_NAME': 'server.test',
            'SERVER_PORT': '8082',
            'SERVER_PROTOCOL': 'http',
            'SCRIPT_NAME': '/v1',
            'PATH_INFO': path,
            'wsgi.url_scheme': 'http',
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
        }

    def _simple_request(self, path, params=None, method='GET',
                        user=DEFAULT_USER, tenant=DEFAULT_TENANT):
        """Returns a request with a fake but valid-looking context

        Returns a request with a fake but valid-looking context
        and sets the request environment variables. If `params` is given,
        it should be a dictionary or sequence of tuples.
        """
        environ = self._environ(path)
        environ['REQUEST_METHOD'] = method

        if params:
            qs = urllib.parse.urlencode(params)
            environ['QUERY_STRING'] = qs

        req = wsgi.Request(environ)
        req.context = utils.dummy_context(user, tenant,
                                          is_admin=self.is_admin)
        self.context = req.context
        return req

    def _get(self, path, params=None, user=DEFAULT_USER,
             tenant=DEFAULT_TENANT):
        return self._simple_request(path, params=params, user=user,
                                    tenant=tenant)

    def _get_with_accept(self, path, params=None, user=DEFAULT_USER,
                         tenant=DEFAULT_TENANT,
                         accept='application/octet-stream'):
        req = self._simple_request(path, params=params, user=user,
                                   tenant=tenant)
        req.accept = accept
        return req

    def _delete(self, path, params=None, user=DEFAULT_USER,
                tenant=DEFAULT_TENANT):
        if params is None:
            params = {}
        return self._simple_request(path, params=params, method='DELETE',
                                    user=user, tenant=tenant)

    def _data_request(self, path, data, content_type='application/json',
                      method='POST', params=None,
                      user=DEFAULT_USER, tenant=DEFAULT_TENANT):
        if params is None:
            params = {}
        environ = self._environ(path)
        environ['REQUEST_METHOD'] = method

        req = wsgi.Request(environ)
        req.context = utils.dummy_context(user, tenant,
                                          is_admin=self.is_admin)
        self.context = req.context
        req.content_type = content_type
        req.body = data

        if params:
            qs = urllib.parse.urlencode(params)
            environ['QUERY_STRING'] = qs

        return req

    def _post(self, path, data, content_type='application/json', params=None,
              user=DEFAULT_USER, tenant=DEFAULT_TENANT):
        if params is None:
            params = {}
        return self._data_request(path, data, content_type, params=params,
                                  user=user, tenant=tenant)

    def _put(self, path, data, content_type='application/json', params=None,
             user=DEFAULT_USER, tenant=DEFAULT_TENANT):
        if params is None:
            params = {}
        return self._data_request(path, data, content_type, method='PUT',
                                  params=params, user=user, tenant=tenant)

    def _patch(self, path, data,
               content_type='application/murano-packages-json-patch',
               params=None, user=DEFAULT_USER, tenant=DEFAULT_TENANT):
        if params is None:
            params = {}
        return self._data_request(path, data, content_type, method='PATCH',
                                  params=params, user=user, tenant=tenant)

    def _set_policy_rules(self, rules):
        policy.set_rules(rules, default_rule='default')

    def expect_policy_check(self, action, target=None):
        if target is None:
            target = {}
        self._policy_check_expectations.append((action, target))

    def _assert_policy_checks(self):
        self.assertEqual(self._policy_check_expectations,
                         self._actual_policy_checks)

    def tearDown(self):
        self._assert_policy_checks()
        policy.reset()
        super(ControllerTest, self).tearDown()
