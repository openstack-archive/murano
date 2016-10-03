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

from murano.api import versions

from murano.api.middleware import version_negotiation

from murano.tests.unit import base


class MiddlewareVersionNegotiationTest(base.MuranoTestCase):

    def test_middleware_version_negotiation_default(self):
        middleware_vn = version_negotiation.VersionNegotiationFilter(None)
        request = webob.Request.blank('/environments')
        result = middleware_vn.process_request(request)
        self.assertIsInstance(result, versions.Controller)
