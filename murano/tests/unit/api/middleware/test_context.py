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

import webob

from murano.api.middleware import context
from murano.tests.unit import base

from oslo_config import cfg

CONF = cfg.CONF


class MiddlewareContextTest(base.MuranoTestCase):

    def test_middleware_context_default(self):
        middleware = context.ContextMiddleware(None)
        request_headers = {
            'X-Roles': 'admin',
            'X-User-Id': "",
            'X-Tenant-Id': "",
            'X-Configuration-Session': "",
        }
        request = webob.Request.blank('/environments',
                                      headers=request_headers)
        self.assertFalse(hasattr(request, 'context'))
        middleware.process_request(request)
        self.assertTrue(hasattr(request, 'context'))

    def test_factory_returns_filter(self):
        middleware = context.ContextMiddleware(None)
        result = middleware.factory(CONF)
        self.assertIsNotNone(result)
