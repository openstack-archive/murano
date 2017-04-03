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

from murano.api.middleware import version_negotiation
from murano.api import versions
from murano.tests.unit import base


class MiddlewareVersionNegotiationTest(base.MuranoTestCase):

    @mock.patch.object(version_negotiation, 'LOG')
    def test_middleware_version_negotiation_default(self, mock_log):
        middleware_vn = version_negotiation.VersionNegotiationFilter(None)
        request = webob.Request.blank('/environments')

        result = middleware_vn.process_request(request)

        self.assertIsInstance(result, versions.Controller)
        mock_log.warning.assert_called_once_with(
            "Unknown version. Returning version choices.")

    @mock.patch.object(version_negotiation, 'LOG')
    def test_process_request(self, mock_log):
        """Test process_request using different valid paths."""
        middleware_vn = version_negotiation.VersionNegotiationFilter(None)

        for path in ('v1', '/v1', '///v1'):
            request = webob.Request.blank(path)
            request.method = 'GET'
            request.environ = {}

            result = middleware_vn.process_request(request)

            self.assertIsNone(result)
            self.assertIn('api.version', request.environ)
            self.assertEqual(1, request.environ['api.version'])
            self.assertEqual('/v1', request.path_info)
            mock_log.debug.assert_any_call(
                "Matched version: v{version}".format(version=1))
            mock_log.debug.assert_any_call(
                'new path {path}'.format(path='/v1'))

        request = webob.Request.blank('/v1/')
        request.method = 'GET'
        request.environ = {}

        result = middleware_vn.process_request(request)

        self.assertIsNone(result)
        self.assertIn('api.version', request.environ)
        self.assertEqual(1, request.environ['api.version'])
        self.assertEqual('/v1/', request.path_info)
        mock_log.debug.assert_any_call(
            "Matched version: v{version}".format(version=1))
        mock_log.debug.assert_any_call(
            'new path {path}'.format(path='/v1/'))

    @mock.patch.object(version_negotiation, 'LOG')
    def test_process_request_without_path(self, mock_log):
        middleware_vn = version_negotiation.VersionNegotiationFilter(None)

        request = webob.Request.blank('')
        request.method = 'GET'
        request.environ = {}

        result = middleware_vn.process_request(request)

        self.assertIsInstance(result, versions.Controller)
        mock_log.warning.assert_called_once_with(
            "Unknown version. Returning version choices.")

    def test_factory(self):
        app = version_negotiation.VersionNegotiationFilter.factory(None)
        self.assertIsNotNone(app)
        self.assertEqual(
            version_negotiation.VersionNegotiationFilter, type(app(None)))
