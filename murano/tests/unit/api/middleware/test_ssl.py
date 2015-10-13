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

import webob

from murano.api.middleware import ssl

from murano.tests.unit import base


class SSLMiddlewareTest(base.MuranoTestCase):

    def test_ssl_middleware_default_forwarded_proto(self):
        middleware = ssl.SSLMiddleware(None)
        request = webob.Request.blank('/environments',
                                      headers={'X-Forwarded-Proto': 'https'})
        middleware.process_request(request)
        self.assertEqual('https',
                         request.environ['wsgi.url_scheme'])

    def test_ssl_middleware_custon_forwarded_proto(self):
        self.override_config('secure_proxy_ssl_header',
                             'X-My-Forwarded-Proto')
        middleware = ssl.SSLMiddleware(None)
        request = webob.Request.blank('/environments',
                                      headers={
                                          'X-My-Forwarded-Proto': 'https'})
        middleware.process_request(request)
        self.assertEqual('https',
                         request.environ['wsgi.url_scheme'])

    def test_ssl_middleware_plain_request(self):
        middleware = ssl.SSLMiddleware(None)
        request = webob.Request.blank('/environments', headers={})
        middleware.process_request(request)
        self.assertEqual('http',
                         request.environ['wsgi.url_scheme'])
