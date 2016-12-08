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

from murano.dsl import context_manager
from murano.dsl import yaql_integration
from murano.tests.unit.dsl.foundation import test_case


class TestContextManager(test_case.DslTestCase):
    def setUp(self):
        super(TestContextManager, self).setUp()
        self.context_manager = context_manager.ContextManager()

    @mock.patch.object(yaql_integration, 'create_context', return_value='foo')
    def test_create_root_context(self, mock_create_context):
        val = self.context_manager.create_root_context('myrunver')

        self.assertEqual('foo', val)
        mock_create_context.assert_called_with('myrunver')

    def test_create_package_context(self):
        package = mock.MagicMock(context='mycontext')
        self.assertEqual('mycontext',
                         self.context_manager.create_package_context(package))

    def test_create_type_context(self):
        murano_type = mock.MagicMock(context='mycontext')
        self.assertEqual('mycontext',
                         self.context_manager.create_type_context(murano_type))

    def test_create_object_context(self):
        obj = 'obj'
        self.assertIsNone(self.context_manager.create_object_context(obj))
