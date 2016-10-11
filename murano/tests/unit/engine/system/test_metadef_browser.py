#    Copyright (c) 2016 AT&T
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

from murano.dsl import murano_object
from murano.engine.system import metadef_browser
from murano.tests.unit import base


class TestMetadefBrowser(base.MuranoTestCase):
    def setUp(self):
        super(TestMetadefBrowser, self).setUp()
        self.this = mock.MagicMock()

        self.glance_client_mock = mock.MagicMock()
        metadef_browser.MetadefBrowser._get_client = mock.MagicMock(
            return_value=self.glance_client_mock)
        metadef_browser.MetadefBrowser._client = mock.MagicMock(
            return_value=self.glance_client_mock)

        self.mock_object = mock.Mock(spec=murano_object.MuranoObject)

    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_get_objects(self, execution_session):
        namespace = None
        self.metadef = metadef_browser.MetadefBrowser(self.this)
        self.assertIsNotNone(self.metadef.get_objects(namespace))
        self.assertTrue(execution_session.called)
        self.assertTrue(metadef_browser.MetadefBrowser.
                        _client.metadefs_object.list.called)

    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_get_namespaces(self, execution_session):
        self.metadef = metadef_browser.MetadefBrowser(self.this)
        resource_type = self.mock_object
        self.assertIsNotNone(self.metadef.get_namespaces(resource_type))
        self.assertTrue(execution_session.called)
        self.assertTrue(metadef_browser.MetadefBrowser.
                        _client.metadefs_namespace.list.called)
