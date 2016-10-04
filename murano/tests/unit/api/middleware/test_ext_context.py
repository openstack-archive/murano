# Copyright 2016 AT&T Corp
# All Rights Reserved.
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
import webob

from keystoneauth1 import exceptions

from murano.api.middleware import ext_context
from murano.tests.unit import base

from oslo_serialization import base64


class MiddlewareExtContextTest(base.MuranoTestCase):

    def test_middleware_ext_context_default(self):
        middleware = ext_context.ExternalContextMiddleware(None)
        middleware.get_keystone_token = mock.MagicMock(return_value="token?")
        auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        request_headers = {
            'Authorization': auth,
        }
        request = webob.Request.blank('/environments',
                                      headers=request_headers)
        middleware.process_request(request)
        self.assertEqual(request.headers.get('X-Auth-Token'), "token?")

    def test_middleware_ext_context_except_key_error(self):
        middleware = ext_context.ExternalContextMiddleware(None)
        middleware.get_keystone_token = mock.MagicMock(
            side_effect=KeyError('test key error')
        )
        auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        request_headers = {
            'Authorization': auth,
        }
        request = webob.Request.blank('/environments',
                                      headers=request_headers)
        self.assertRaises(webob.exc.HTTPUnauthorized,
                          middleware.process_request, request)

    def test_middleware_ext_context_except_unauthorized(self):
        middleware = ext_context.ExternalContextMiddleware(None)
        middleware.get_keystone_token = mock.MagicMock(
            side_effect=exceptions.Unauthorized('')
        )
        auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        request_headers = {
            'Authorization': auth,
        }
        request = webob.Request.blank('/environments',
                                      headers=request_headers)
        self.assertRaises(webob.exc.HTTPUnauthorized,
                          middleware.process_request, request)

    @mock.patch('murano.api.middleware.ext_context.ks_session')
    @mock.patch('murano.api.middleware.ext_context.v3')
    @mock.patch('murano.api.middleware.ext_context.CONF')
    def test_get_keystone_token(self, mock_conf, mock_v3, mock_ks_session):
        mock_ks_session.Session().get_token.return_value = 'test_token'
        test_auth_urls = ['test_url', 'test_url/v2.0', 'test_url/v3']

        for url in test_auth_urls:
            mock_conf.cfapi = mock.MagicMock(auth_url=url,
                                             tenant='test_tenant',
                                             user_domain_name='test_udn',
                                             project_domain_name='test_pdn')

            middleware = ext_context.ExternalContextMiddleware(None)
            token = middleware.get_keystone_token('test_user', 'test_password')
            self.assertEqual('test_token', token)

            expected_kwargs = {
                'auth_url': 'test_url/v3',
                'username': 'test_user',
                'password': 'test_password',
                'project_name': mock_conf.cfapi.tenant,
                'user_domain_name': mock_conf.cfapi.user_domain_name,
                'project_domain_name': mock_conf.cfapi.project_domain_name
            }
            mock_v3.Password.assert_called_once_with(**expected_kwargs)
            mock_v3.Password.reset_mock()

    def test_query_endpoints_except_endpoint_not_found(self):
        middleware = ext_context.ExternalContextMiddleware(None)
        if hasattr(middleware, '_murano_endpoint'):
            setattr(middleware, '_murano_endpoint', None)
        mock_auth = mock.MagicMock()
        mock_auth.get_endpoint.side_effect = exceptions.EndpointNotFound

        middleware._query_endpoints(mock_auth, 'test_session')
        mock_auth.get_endpoint.assert_any_call('test_session',
                                               'application-catalog')

        if hasattr(middleware, '_glare_endpoint'):
            setattr(middleware, '_glare_endpoint', None)
        setattr(middleware, '_murano_endpoint', 'test_endpoint')

        middleware._query_endpoints(mock_auth, 'test_session')
        mock_auth.get_endpoint.assert_any_call('test_session',
                                               'artifact')
