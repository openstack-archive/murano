# Copyright (c) 2016 AT&T
# All Rights Reserved.
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

import random

try:
    from mistralclient.api import client as mistralcli
except ImportError as mistral_import_error:
    mistralcli = None

import mock
from oslo_config import cfg

from murano.dsl import murano_method
from murano.dsl import murano_type

from murano.engine.system import workflowclient
from murano.tests.unit import base


CONF = cfg.CONF


def rand_name(name='murano'):
    """Generates random string.

    :param name: Basic name
    :return:
    """
    return name + str(random.randint(1, 0x7fffffff))


class TestMistralClient(base.MuranoTestCase):
    def setUp(self):
        super(TestMistralClient, self).setUp()
        self.mistral_client_mock = mock.Mock()
        self.mistral_client_mock.client = mock.MagicMock(
            spec=mistralcli.client)
        self._patch_client()

        self.mock_class = mock.MagicMock(spec=murano_type.MuranoClass)
        self.mock_method = mock.MagicMock(spec=murano_method.MuranoMethod)

        self._this = mock.MagicMock()
        self._this.owner = None

        self.addCleanup(mock.patch.stopall)

    def _patch_client(self):
        self.mock_client = mock.Mock(return_value=self.mistral_client_mock)
        self.client_patcher = mock.patch.object(workflowclient.MistralClient,
                                                '_client', self.mock_client)
        self.client_patcher.start()

        self.mock_create_client = mock.Mock(
            return_value=self.mistral_client_mock)
        self.create_client_patcher = mock.patch.object(
            workflowclient.MistralClient, '_create_client',
            self.mock_create_client)
        self.create_client_patcher.start()

    def _unpatch_client(self):
        self.client_patcher.stop()
        self.create_client_patcher.stop()

    def test_run_with_execution_success_state(self):
        test_output = '{"openstack": "foo", "__execution": "bar", "task":'\
                      ' "baz"}'
        mock_execution = mock.MagicMock(
            id='123', state='SUCCESS', output=test_output)
        self.mock_client.executions.create.return_value = mock_execution
        self.mock_client.executions.get.return_value = mock_execution

        run_name = rand_name('test')
        timeout = 1
        mc = workflowclient.MistralClient(self._this, 'regionOne')
        output = mc.run(run_name, timeout)

        for prop in ['openstack', '__execution', 'task']:
            self.assertFalse(hasattr(output, prop))

        self.assertEqual({}, output)

    def test_run_with_execution_error_state(self):
        mock_execution = mock.MagicMock(
            id='123', state='ERROR', output="{'test_attr': 'test_val'}")
        self.mock_client.executions.create.return_value = mock_execution
        self.mock_client.executions.get.return_value = mock_execution

        run_name = rand_name('test')
        timeout = 1
        mc = workflowclient.MistralClient(self._this, 'regionOne')

        expected_error_msg = 'Mistral execution completed with ERROR.'\
                             ' Execution id: {0}. Output: {1}'\
                             .format(mock_execution.id, mock_execution.output)
        with self.assertRaisesRegex(workflowclient.MistralError,
                                    expected_error_msg):
            mc.run(run_name, timeout)

    def test_run_except_timeout_error(self):
        mock_execution = mock.MagicMock(
            id='123', state='TEST_STATE', output="{'test_attr': 'test_val'}")
        self.mock_client.executions.create.return_value = mock_execution
        self.mock_client.executions.get.return_value = mock_execution

        run_name = rand_name('test')
        timeout = 1
        mc = workflowclient.MistralClient(self._this, 'regionOne')

        expected_error_msg = 'Mistral run timed out. Execution id: {0}.'\
                             .format(mock_execution.id)
        with self.assertRaisesRegex(workflowclient.MistralError,
                                    expected_error_msg):
            mc.run(run_name, timeout)

    def test_run_with_immediate_timeout(self):
        mock_execution = mock.MagicMock(
            id='123', state='ERROR', output="{'test_attr': 'test_val'}")
        self.mock_client.executions.create.return_value = mock_execution

        run_name = rand_name('test')
        timeout = 0
        mc = workflowclient.MistralClient(self._this, 'regionOne')
        self.assertEqual(mock_execution.id, mc.run(run_name, timeout))

    def test_upload(self):
        mc = workflowclient.MistralClient(self._this, 'regionOne')
        definition = rand_name('test')
        self.assertIsNone(mc.upload(definition))
        self.assertTrue(workflowclient.MistralClient.
                        _client.workflows.create.called)

    @mock.patch('murano.engine.system.workflowclient.auth_utils')
    def test_client_property(self, _):
        self._unpatch_client()

        test_mistral_settings = {
            'url': rand_name('test_mistral_url'),
            'project_id': rand_name('test_project_id'),
            'endpoint_type': rand_name('test_endpoint_type'),
            'auth_token': rand_name('test_auth_token'),
            'user_id': rand_name('test_user_id'),
            'insecure': rand_name('test_insecure'),
            'cacert': rand_name('test_ca_cert')
        }

        with mock.patch('murano.engine.system.workflowclient.CONF')\
                as mock_conf:
            mock_conf.mistral = mock.MagicMock(**test_mistral_settings)
            region_name = rand_name('test_region_name')
            mc = workflowclient.MistralClient(self._this, region_name)

            mistral_client = mc._client
            self.assertIsNotNone(mistral_client)
