# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from tempest.api.murano import base
from tempest.test import attr
from tempest import exceptions


class SanityMuranoTest(base.MuranoTest):

    @attr(type='smoke')
    def test_create_session(self):
        """
        Create session
        Test create environment, create session
        and delete session
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session
            3. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, sess = self.create_session(env['id'])
        self.assertEqual(resp['status'], '200')
        resp, infa = self.get_session_info(env['id'], sess['id'])
        self.assertEqual(resp['status'], '200')
        self.assertEqual(infa['environment_id'], env['id'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))

    @attr(type='negative')
    def test_create_session_before_env(self):
        """
        Try to create session without environment
        Target component: Murano

        Scenario:
        1. Send request to create session
        """
        self.assertRaises(exceptions.NotFound, self.create_session,
                          None)

    @attr(type='negative')
    def test_delete_session_with_wrong_env_id(self):
        """
        Try to delete session using uncorrect env_id
        Target component: Murano

        Scenario:
        1. Send request to create environment
        2. Send request to create session
        3. Send request to delete session using uncorrect env_id
        4. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, sess = self.create_session(env['id'])
        self.assertRaises(exceptions.NotFound, self.delete_session, None,
                          sess['id'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))

    @attr(type='negative')
    def test_create_session_with_wrong_env_id(self):
        """
        Try to create session using uncorrect env_id
        Target component: Murano

        Scenario:
        1. Send request to create environment
        2. Send request to create session using uncorrect env_id
        3. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        self.assertRaises(exceptions.NotFound, self.create_session,
                          None)
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))

    @attr(type='negative')
    def test_get_session_info_wo_env_id(self):
        """
        Try to get session info without env_id
        Target component: Murano

        Scenario:
        1. Send request to create environment
        2. Send request to create session
        3. Send request to get info about session using wrong id
        4. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, sess = self.create_session(env['id'])
        self.assertRaises(exceptions.NotFound, self.get_session_info,
                          None, sess['id'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))

    @attr(type='negative')
    def test_get_session_info_after_delete_env(self):
        """
        Try to get session info after delete current environment
        Target component: Murano

        Scenario:
        1. Send request to create environment
        2. Send request to create session
        3. Send request to delete environment
        4. Send request to get info about session
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, sess = self.create_session(env['id'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))
        self.assertRaises(exceptions.NotFound, self.get_session_info,
                          env['id'], sess['id'])

    @attr(type='smoke')
    def test_get_session_info(self):
        """
        Create session
        Test create environment, create session, get info about this session
        and delete session
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session
            3. Send request to get info about created session
            4. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, sess = self.create_session(env['id'])
        resp, infa = self.get_session_info(env['id'], sess['id'])
        self.assertEqual(resp['status'], '200')
        self.assertEqual(infa['environment_id'], env['id'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))

    @attr(type='smoke')
    def test_delete_session(self):
        """
        Create session
        Test create environment, create session, delete created session
        and delete session
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session
            3. Send request to delete created session
            4. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, sess = self.create_session(env['id'])
        self.delete_session(env['id'], sess['id'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))

    @attr(type='negative')
    def test_double_delete_session(self):
        """
        Try to double delete session
        Target component: Murano

        Scenario:
        1. Send request to create environment
        2. Send request to create session
        3. Send request to delete session
        4. Send request to delete session
        5. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, sess = self.create_session(env['id'])
        self.delete_session(env['id'], sess['id'])
        self.assertRaises(exceptions.NotFound, self.delete_session, env['id'],
                          sess['id'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))
