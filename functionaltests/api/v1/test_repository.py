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

from tempest.test import attr

from functionaltests.api import base


class TestRepository(base.TestCase):

    @classmethod
    def setUpClass(cls):

        super(TestRepository, cls).setUpClass()

        raise cls.skipException("Murano Repository tests are disabled")

    @attr(type='smoke')
    def test_get_list_packages(self):
        resp, body = self.client.get_list_packages()

        self.assertEqual(200, resp.status)
        self.assertTrue(isinstance(body['packages'], list))

    @attr(type='smoke')
    def test_get_package(self):
        _, body = self.client.get_list_packages()
        package = body['packages'][0]

        resp, body = self.client.get_package(package['id'])

        self.assertEqual(200, resp.status)
        self.assertEqual(package, body)

    @attr(type='smoke')
    def test_update_package(self):
        _, body = self.client.get_list_packages()
        package = body['packages'][0]

        resp, body = self.client.update_package(package['id'])

        self.assertEqual(200, resp.status)
        self.assertIn("i'm a test", body['tags'])

    @attr(type='smoke')
    def test_delete_package(self):
        _, body = self.client.get_list_packages()
        package = body['packages'][0]

        resp, _ = self.client.delete_package(package['id'])

        self.assertEqual(200, resp.status)

    @attr(type='smoke')
    def test_download_package(self):
        _, body = self.client.get_list_packages()
        package = body['packages'][0]

        resp, _ = self.client.download_package(package['id'])

        self.assertEqual(200, resp.status)

    @attr(type='smoke')
    def test_get_ui_definitions(self):
        _, body = self.client.get_list_packages()
        package = body['packages'][0]

        resp, _ = self.client.get_ui_definition(package['id'])

        self.assertEqual(200, resp.status)

    @attr(type='smoke')
    def test_get_logo(self):
        _, body = self.client.get_list_packages()
        package = body['packages'][0]

        resp, _ = self.client.get_logo(package['id'])

        self.assertEqual(200, resp.status)

    @attr(type='smoke')
    def test_get_list_categories(self):
        resp, body = self.client.list_categories()

        self.assertEqual(200, resp.status)
        self.assertTrue(isinstance(body['categories'], list))
