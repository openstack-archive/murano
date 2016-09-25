#    Copyright (c) 2014 Mirantis, Inc.
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

from murano.services import actions
from murano.tests.unit import base


class TestActionFinder(base.MuranoTestCase):
    def test_simple_root_level_search(self):
        model = {
            '?': {
                'id': 'id1',
                '_actions': {
                    'ad_deploy': {
                        'enabled': True,
                        'name': 'deploy'
                    }
                }
            }
        }
        action = actions.ActionServices.find_action(model, 'ad_deploy')
        self.assertEqual('deploy', action[1]['name'])

    def test_recursive_action_search(self):
        model = {
            '?': {
                'id': 'id1',
                '_actions': {'ad_deploy': {'enabled': True, 'name': 'deploy'}}
            },
            'property': {
                '?': {
                    'id': 'id2',
                    '_actions': {
                        'ad_scale': {'enabled': True, 'name': 'scale'}
                    }
                },
            }
        }
        action = actions.ActionServices.find_action(model, 'ad_scale')
        self.assertEqual('scale', action[1]['name'])
