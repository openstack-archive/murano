# Copyright (c) 2016 AT&T
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

from murano.api.v1 import instance_statistics
import murano.tests.unit.api.base as tb


class TestInstanceStatistics(tb.ControllerTest, tb.MuranoApiTestCase):
    def setUp(self):
        super(TestInstanceStatistics, self).setUp()
        self.controller = instance_statistics.Controller()

    def test_get_aggregated(self):
        self._set_policy_rules(
            {"get_aggregated_statistics": "@"}
        )
        self.expect_policy_check("get_aggregated_statistics",
                                 {'environment_id': u'12344'})
        env_id = 12344

        req = self._get('/environments/{env_id}/'
                        'instance-statistics/aggregated'
                        .format(env_id=env_id))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

    def test_get_for_instance(self):
        self._set_policy_rules(
            {"get_instance_statistics": "@"}
        )
        self.expect_policy_check("get_instance_statistics",
                                 {'environment_id': u'12345',
                                  'instance_id': u'12'})
        env_id = 12345
        ins_id = 12

        req = self._get('/environments/{env_id}/'
                        'instance-statistics/raw/{ins_id}'
                        .format(env_id=env_id, ins_id=ins_id))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

    def test_get_for_env(self):
        self._set_policy_rules(
            {"get_statistics": "@"}
        )
        self.expect_policy_check("get_statistics",
                                 {'environment_id': u'12346'})
        env_id = 12346

        req = self._get('/environments/{env_id}/instance-statistics/raw'
                        .format(env_id=env_id))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
