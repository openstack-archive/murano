# Copyright (c) 2016 AT&T Corp
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

import mock
from oslo_messaging.rpc import client
from webob import exc

from murano.api.v1 import schemas
import murano.tests.unit.base as test_base
from murano.tests.unit import utils as test_utils


@mock.patch('murano.api.v1.schemas.policy')
@mock.patch('murano.api.v1.schemas.request_statistics.update_error_count')
@mock.patch('murano.api.v1.schemas.request_statistics.update_count')
class TestSchemas(test_base.MuranoTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestSchemas, cls).setUpClass()
        cls.controller = schemas.Controller()

    @mock.patch('murano.api.v1.schemas.rpc')
    def test_get_schema(self, mock_rpc, *args):
        dummy_context = test_utils.dummy_context()
        dummy_context.GET = {
            'classVersion': 'test_class_version',
            'packageName': 'test_package_name'
        }
        mock_request = mock.MagicMock(context=dummy_context)
        mock_rpc.engine().generate_schema.return_value = 'test_schema'

        result = self.controller.get_schema(mock_request, 'test_class')
        self.assertEqual('test_schema', result)

    @mock.patch('murano.api.v1.schemas.rpc')
    def test_get_schema_negative(self, mock_rpc, *args):
        dummy_context = test_utils.dummy_context()
        dummy_context.GET = {
            'classVersion': 'test_class_version',
            'packageName': 'test_package_name'
        }
        mock_request = mock.MagicMock(context=dummy_context)

        # Test exception handling for pre-defined exception types.
        exc_types = ('NoClassFound',
                     'NoPackageForClassFound',
                     'NoPackageFound')
        for exc_type in exc_types:
            dummy_error = client.RemoteError(exc_type=exc_type,
                                             value='dummy_value')
            mock_rpc.engine().generate_schema.side_effect = dummy_error
            with self.assertRaisesRegex(exc.HTTPNotFound,
                                        dummy_error.value):
                self.controller.get_schema(mock_request, 'test_class')

        # Test exception handling for miscellaneous exception type.
        dummy_error = client.RemoteError(exc_type='TestExcType',
                                         value='dummy_value')
        mock_rpc.engine().generate_schema.side_effect = dummy_error
        with self.assertRaisesRegex(client.RemoteError,
                                    dummy_error.value):
            self.controller.get_schema(mock_request, 'test_class')
