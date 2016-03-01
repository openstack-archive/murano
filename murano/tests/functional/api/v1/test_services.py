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

from tempest.lib import exceptions
from tempest.test import attr

from murano.tests.functional.api import base


class TestServices(base.TestCase):

    @attr(type='smoke')
    def test_get_services_list(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        resp, services_list = self.client.get_services_list(env['id'],
                                                            sess['id'])

        self.assertEqual(resp.status, 200)
        self.assertTrue(isinstance(services_list, list))

    @attr(type='negative')
    def test_get_services_list_without_env_id(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        self.assertRaises(exceptions.NotFound,
                          self.client.get_services_list,
                          None,
                          sess['id'])

    @attr(type='negative')
    def test_get_services_list_after_delete_env(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        self.client.delete_environment(env['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.get_services_list,
                          env['id'],
                          sess['id'])

    @attr(type='negative')
    def test_get_services_list_after_delete_session(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        self.client.delete_session(env['id'], sess['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.get_services_list,
                          env['id'],
                          sess['id'])

    @attr(type='smoke')
    def test_create_and_delete_demo_service(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        services_list = self.client.get_services_list(env['id'], sess['id'])[1]

        resp, service = self.create_demo_service(env['id'], sess['id'])

        services_list_ = self.client.get_services_list(env['id'],
                                                       sess['id'])[1]

        self.assertEqual(resp.status, 200)
        self.assertEqual(len(services_list) + 1, len(services_list_))

        resp = self.client.delete_service(env['id'],
                                          sess['id'],
                                          service['?']['id'])[0]

        services_list_ = self.client.get_services_list(env['id'],
                                                       sess['id'])[1]

        self.assertEqual(resp.status, 200)
        self.assertEqual(len(services_list), len(services_list_))

    @attr(type='negative')
    def test_create_demo_service_without_env_id(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        self.assertRaises(exceptions.NotFound,
                          self.create_demo_service,
                          None,
                          sess['id'])

    @attr(type='negative')
    def test_create_demo_service_without_sess_id(self):
        env = self.create_environment('test')

        self.client.create_session(env['id'])

        self.assertRaises(exceptions.Forbidden,
                          self.create_demo_service,
                          env['id'],
                          "")

    @attr(type='negative')
    def test_delete_demo_service_without_env_id(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        service = self.create_demo_service(env['id'], sess['id'])[1]

        self.assertRaises(exceptions.NotFound,
                          self.client.delete_service,
                          None,
                          sess['id'],
                          service['?']['id'])

    @attr(type='negative')
    def test_delete_demo_service_without_session_id(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        service = self.create_demo_service(env['id'], sess['id'])[1]

        self.assertRaises(exceptions.Forbidden,
                          self.client.delete_service,
                          env['id'],
                          "",
                          service['?']['id'])

    @attr(type='negative')
    def test_double_delete_service(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        service = self.create_demo_service(env['id'], sess['id'])[1]

        self.client.delete_service(env['id'], sess['id'], service['?']['id'])

        self.assertRaises(exceptions.NotFound,
                          self.client.delete_service,
                          env['id'],
                          sess['id'],
                          service['?']['id'])

    @attr(type='smoke')
    def test_get_service(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        service = self.create_demo_service(env['id'], sess['id'])[1]

        resp, service_ = self.client.get_service(env['id'],
                                                 sess['id'],
                                                 service['?']['id'])

        self.assertEqual(resp.status, 200)
        self.assertEqual(service, service_)

    @attr(type='negative')
    def test_get_service_without_env_id(self):
        env = self.create_environment('test')

        sess = self.client.create_session(env['id'])[1]

        service = self.create_demo_service(env['id'], sess['id'])[1]

        self.assertRaises(exceptions.NotFound,
                          self.client.get_service,
                          None,
                          sess['id'],
                          service['?']['id'])

    @attr(type='smoke')
    def test_get_services_without_sess_id(self):
        env = self.create_environment('test')
        resp, body = self.client.get_services_list(env['id'], None)
        self.assertEqual(resp.status, 200)
        self.assertEqual([], body)


class TestServicesTenantIsolation(base.NegativeTestCase):

    @attr(type='negative')
    def test_get_list_services_in_env_from_another_tenant(self):
        env = self.create_environment('test')
        sess = self.client.create_session(env['id'])[1]

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.get_services_list, env['id'],
                          sess['id'])

    @attr(type='negative')
    def test_create_service_in_env_from_another_tenant(self):
        env = self.create_environment('test')
        sess = self.client.create_session(env['id'])[1]

        self.assertRaises(exceptions.Unauthorized,
                          self.create_demo_service, env['id'],
                          sess['id'], client=self.alt_client)

    @attr(type='negative')
    def test_delete_service_in_env_from_another_tenant(self):
        env = self.create_environment('test')
        sess = self.client.create_session(env['id'])[1]
        service = self.create_demo_service(env['id'], sess['id'])[1]

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.delete_service, env['id'],
                          sess['id'], service['?']['id'])

    @attr(type='negative')
    def test_get_service_in_env_from_another_tenant(self):
        env = self.create_environment('test')
        sess = self.client.create_session(env['id'])[1]
        service = self.create_demo_service(env['id'], sess['id'])[1]

        self.assertRaises(exceptions.Unauthorized,
                          self.alt_client.get_service, env['id'],
                          sess['id'], service['?']['id'])
