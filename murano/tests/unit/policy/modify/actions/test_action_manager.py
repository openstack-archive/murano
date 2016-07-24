# Copyright (c) 2015 OpenStack Foundation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

import murano.policy.modify.actions.action_manager as am
from murano.policy.modify.actions import default_actions as da
import murano.tests.unit.policy.modify.actions.test_default_actions as tda


class TestActionManager(tda.ModifyActionTestCase):

    def test_loading(self):
        manager = am.ModifyActionManager()
        self.assertEqual(da.RemoveObjectAction,
                         manager.load_action('remove-object'))
        self.assertEqual(da.SetPropertyAction,
                         manager.load_action('set-property'))
        self.assertEqual(da.AddObjectAction,
                         manager.load_action('add-object'))
        self.assertEqual(da.RemoveRelationAction,
                         manager.load_action('remove-relation'))

    def test_caching(self):
        manager = am.ModifyActionManager()
        manager._load_action = mock.MagicMock(wraps=manager._load_action)
        manager.load_action('remove-object')
        # second call is expected to get cached value
        manager.load_action('remove-object')
        manager._load_action.assert_called_once_with('remove-object')

    def test_no_such_action(self):
        manager = am.ModifyActionManager()
        self.assertRaises(ValueError, manager.load_action, 'no-such-action')

    def test_action_apply(self):
        with self._runner.session():
            manager = am.ModifyActionManager()
            obj_id = self._dict_member.id
            action_spec = 'remove-object: {object_id: %s}' % obj_id
            manager.apply_action(self._obj,
                                 action_spec)

    def test_action_apply_invalid_spec(self):
        manager = am.ModifyActionManager()
        self.assertRaises(ValueError,
                          manager.apply_action, self._obj, 'remove-object')
