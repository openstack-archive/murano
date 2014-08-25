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


import mock

from murano.api.v1 import actions
from murano.common import policy
from murano.db import models
from murano.openstack.common import timeutils
import murano.tests.unit.api.base as tb
import murano.tests.unit.utils as test_utils


@mock.patch.object(policy, 'check')
class TestActionsApi(tb.ControllerTest, tb.MuranoApiTestCase):

    def setUp(self):
        super(TestActionsApi, self).setUp()
        self.controller = actions.Controller()

    def test_execute_action(self, mock_policy_check):
        """Test that action execution results in the correct rpc call."""
        self._set_policy_rules(
            {'execute_action': '@'}
        )

        fake_now = timeutils.utcnow()
        expected = dict(
            id='12345',
            name='my-env',
            version=0,
            networking={},
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'Objects': {
                    '?': {'id': '12345',
                          '_actions': {
                              'actionsID_action': {
                                  'enabled': True,
                                  'name': 'Testaction'
                              }
                          }}
                },
                'Attributes': {}
            }
        )
        e = models.Environment(**expected)
        test_utils.save_models(e)

        rpc_task = {
            'tenant_id': self.tenant,
            'model': {'Objects': {'applications': [], '?':
            {
                '_actions': {'actionsID_action': {
                'name': 'Testaction', 'enabled': True}},
                'id': '12345'}}, 'Attributes': {}},
            'action': {
                'method': 'Testaction',
                'object_id': '12345',
                'args': '{}'},
            'token': None,
            'id': '12345'
        }

        req = self._post('/environments/12345/actions/actionID_action', '{}')
        result = self.controller.execute(req, '12345', 'actionsID_action',
                                         '{}')

        self.mock_engine_rpc.handle_task.assert_called_once_with(rpc_task)

        # Should this be expected behavior?
        self.assertEqual(None, result)
