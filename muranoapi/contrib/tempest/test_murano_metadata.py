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

import testtools

from tempest.api.murano import base
from tempest import exceptions
from tempest.test import attr


class SanityMuranoTest(base.MuranoMeta):

    @attr(type='smoke')
    def test_get_list_metadata_objects_ui(self):
        resp, body = self.get_list_metadata_objects("ui")
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_get_list_metadata_objects_workflows(self):
        resp, body = self.get_list_metadata_objects("workflows")
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_get_list_metadata_objects_heat(self):
        resp, body = self.get_list_metadata_objects("heat")
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_get_list_metadata_objects_agent(self):
        resp, body = self.get_list_metadata_objects("agent")
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_get_list_metadata_objects_scripts(self):
        resp, body = self.get_list_metadata_objects("scripts")
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_get_list_metadata_objects_manifests(self):
        resp, body = self.get_list_metadata_objects("manifests")
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='negative')
    def test_get_list_metadata_objects_incorrect_type(self):
        self.assertRaises(exceptions.NotFound, self.get_list_metadata_objects,
                          'someth')

    @attr(type='smoke')
    def test_get_ui_definitions(self):
        resp, body = self.get_ui_definitions()
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_get_conductor_metadata(self):
        resp, body = self.get_conductor_metadata()
        self.assertIsNotNone(body)
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_create_directory_and_delete_workflows(self):
        resp, body = self.create_directory("workflows/", "testdir")
        self.objs.append("workflows/testdir")
        resp1, body1 = self.delete_metadata_obj_or_folder("workflows/testdir")
        self.assertEqual(resp['status'], '200')
        self.assertEqual(resp1['status'], '200')
        self.assertEqual(body['result'], 'success')
        self.assertEqual(body1['result'], 'success')
        self.objs.pop(self.objs.index("workflows/testdir"))

    @attr(type='smoke')
    def test_create_directory_and_delete_ui(self):
        resp, body = self.create_directory("ui/", "testdir")
        self.objs.append("ui/testdir")
        resp1, body1 = self.delete_metadata_obj_or_folder("ui/testdir")
        self.assertEqual(resp['status'], '200')
        self.assertEqual(resp1['status'], '200')
        self.assertEqual(body['result'], 'success')
        self.assertEqual(body1['result'], 'success')
        self.objs.pop(self.objs.index("ui/testdir"))

    @attr(type='smoke')
    def test_create_directory_and_delete_heat(self):
        resp, body = self.create_directory("heat/", "testdir")
        self.objs.append("heat/testdir")
        resp1, body1 = self.delete_metadata_obj_or_folder("heat/testdir")
        self.assertEqual(resp['status'], '200')
        self.assertEqual(resp1['status'], '200')
        self.assertEqual(body['result'], 'success')
        self.assertEqual(body1['result'], 'success')
        self.objs.pop(self.objs.index("heat/testdir"))

    @attr(type='smoke')
    def test_create_directory_and_delete_agent(self):
        resp, body = self.create_directory("agent/", "testdir")
        self.objs.append("agent/testdir")
        resp1, body1 = self.delete_metadata_obj_or_folder("agent/testdir")
        self.assertEqual(resp['status'], '200')
        self.assertEqual(resp1['status'], '200')
        self.assertEqual(body['result'], 'success')
        self.assertEqual(body1['result'], 'success')
        self.objs.pop(self.objs.index("agent/testdir"))

    @attr(type='smoke')
    def test_create_directory_and_delete_scripts(self):
        resp, body = self.create_directory("scripts/", "testdir")
        self.objs.append("scripts/testdir")
        resp1, body1 = self.delete_metadata_obj_or_folder("scripts/testdir")
        self.assertEqual(resp['status'], '200')
        self.assertEqual(resp1['status'], '200')
        self.assertEqual(body['result'], 'success')
        self.assertEqual(body1['result'], 'success')
        self.objs.pop(self.objs.index("scripts/testdir"))

    @testtools.skip('Bug https://bugs.launchpad.net/murano/+bug/1268934')
    @attr(type='negative')
    def test_create_directory_manifests(self):
        self.assertRaises(exceptions.Unauthorized, self.create_directory,
                          "manifests/", "testdir")

    @attr(type='negative')
    def test_create_directory_incorrect_type(self):
        self.assertRaises(exceptions.NotFound, self.create_directory,
                          "someth/", "testdir")

    @attr(type='smoke')
    def test_double_create_directory(self):
        self.create_directory("workflows/", "testdir")
        self.objs.append("workflows/testdir")
        resp, body = self.create_directory("workflows/", "testdir")
        self.assertEqual(resp['status'], '200')
        self.assertEqual(body['result'], 'success')
        self.delete_metadata_obj_or_folder("workflows/testdir")
        self.objs.pop(self.objs.index("workflows/testdir"))

    @attr(type='negative')
    def test_delete_nonexistent_object(self):
        self.assertRaises(exceptions.NotFound,
                          self.delete_metadata_obj_or_folder,
                          "somth/blabla")

    @attr(type='negative')
    def test_delete_basic_folder(self):
        self.assertRaises(exceptions.MethodNotAllowed,
                          self.delete_metadata_obj_or_folder,
                          "workflows")

    @attr(type='negative')
    def test_create_basic_folder(self):
        self.assertRaises(exceptions.MethodNotAllowed, self.create_directory,
                          "", "somth")

    @attr(type='negative')
    def test_double_upload_file(self):
        self.upload_metadata_object(path="workflows")
        self.objs.append("workflows/testfile.txt")
        resp = self.upload_metadata_object(path="workflows")
        self.assertEqual(resp.status_code, 403)
        self.delete_metadata_obj_or_folder("workflows/testfile.txt")
        self.objs.pop(self.objs.index("workflows/testfile.txt"))

    @attr(type='negative')
    def test_upload_file_incorrect(self):
        resp = self.upload_metadata_object(path="workflows/testfil")
        self.assertEqual(resp.status_code, 404)

    @attr(type='smoke')
    def test_upload_file_and_delete_workflows(self):
        resp = self.upload_metadata_object(path="workflows")
        self.objs.append("workflows/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("workflows")
        self.delete_metadata_obj_or_folder("workflows/testfile.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        self.objs.pop(self.objs.index("workflows/testfile.txt"))

    @attr(type='smoke')
    def test_upload_file_and_delete_ui(self):
        resp = self.upload_metadata_object(path="ui")
        self.objs.append("ui/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("ui")
        self.delete_metadata_obj_or_folder("ui/testfile.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        self.objs.pop(self.objs.index("ui/testfile.txt"))

    @attr(type='smoke')
    def test_upload_file_and_delete_heat(self):
        resp = self.upload_metadata_object(path="heat")
        self.objs.append("heat/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("heat")
        self.delete_metadata_obj_or_folder("heat/testfile.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        self.objs.pop(self.objs.index("heat/testfile.txt"))

    @attr(type='smoke')
    def test_upload_file_and_delete_agent(self):
        resp = self.upload_metadata_object(path="agent")
        self.objs.append("agent/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("agent")
        self.delete_metadata_obj_or_folder("agent/testfile.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        self.objs.pop(self.objs.index("agent/testfile.txt"))

    @attr(type='smoke')
    def test_upload_file_and_delete_scripts(self):
        resp = self.upload_metadata_object(path="scripts")
        self.objs.append("scripts/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("scripts")
        self.delete_metadata_obj_or_folder("scripts/testfile.txt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        self.objs.pop(self.objs.index("scripts/testfile.txt"))

    @attr(type='smoke')
    def test_upload_file_and_delete_manifests(self):
        resp = self.upload_metadata_object(path="manifests",
                                           filename='testfile-manifest.yaml')
        self.objs.append("manifests/testfile-manifest.yaml")
        resp1, body1 = self.get_list_metadata_objects("manifests")
        self.delete_metadata_obj_or_folder("manifests/testfile-manifest.yaml")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile-manifest.yaml', body1)
        self.objs.pop(self.objs.index("manifests/testfile-manifest.yaml"))

    @attr(type='smoke')
    def test_get_metadata_object(self):
        self.upload_metadata_object(path="workflows")
        self.objs.append("workflows/testfile.txt")
        resp1, body1 = self.get_metadata_object("workflows/testfile.txt")
        self.delete_metadata_obj_or_folder("workflows/testfile.txt")
        self.assertEqual(resp1['status'], '200')
        self.assertIsNotNone(body1)
        self.objs.pop(self.objs.index("workflows/testfile.txt"))

    @attr(type='negative')
    def test_get_nonexistent_metadata_object(self):
        self.assertRaises(exceptions.NotFound, self.get_metadata_object,
                          "somth/blabla")

    @testtools.skip('Bug https://bugs.launchpad.net/murano/+bug/1249303')
    @attr(type='negative')
    def test_delete_nonempty_folder_in_workflows(self):
        self.create_directory("workflows/", "testdir")
        self.objs.append("workflows/testdir")
        self.upload_metadata_object(path="workflows/testdir")
        self.objs.append("workflows/testdir/testfile.txt")
        self.assertRaises(Exception, self.delete_metadata_obj_or_folder,
                          "workflows/testdir")
        self.delete_metadata_obj_or_folder("workflows/testdir/testfile.txt")
        self.delete_metadata_obj_or_folder("workflows/testdir")
        self.objs.pop(self.objs.index("workflows/testdir"))
        self.objs.pop(self.objs.index("workflows/testdir/testfile.txt"))

    @attr(type='positive')
    def test_create_folder_and_upload_file_workflows(self):
        self.create_directory("workflows/", "testdir")
        self.objs.append("workflows/testdir")
        resp = self.upload_metadata_object(path="workflows/testdir")
        self.objs.append("workflows/testdir/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("workflows/testdir")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        resp, _ =\
            self.delete_metadata_obj_or_folder(
                "workflows/testdir/testfile.txt")
        self.assertEqual(resp['status'], '200')
        resp, _ = self.delete_metadata_obj_or_folder("workflows/testdir")
        self.assertEqual(resp['status'], '200')
        resp, body = self.get_list_metadata_objects("workflows")
        self.assertEqual(resp['status'], '200')
        self.assertNotIn('testfile.txt', body)
        self.objs.pop(self.objs.index("workflows/testdir"))
        self.objs.pop(self.objs.index("workflows/testdir/testfile.txt"))

    @testtools.skip('Bug https://bugs.launchpad.net/murano/+bug/1249303')
    @attr(type='negative')
    def test_delete_nonempty_folder_in_ui(self):
        self.create_directory("ui/", "testdir")
        self.objs.append("ui/testdir")
        self.upload_metadata_object(path="ui/testdir")
        self.objs.append("ui/testdir/testfile.txt")
        self.assertRaises(Exception, self.delete_metadata_obj_or_folder,
                          "ui/testdir")
        self.delete_metadata_obj_or_folder("ui/testdir/testfile.txt")
        self.delete_metadata_obj_or_folder("ui/testdir")
        self.objs.pop(self.objs.index("ui/testdir"))
        self.objs.pop(self.objs.index("ui/testdir/testfile.txt"))

    @attr(type='positive')
    def test_create_folder_and_upload_file_ui(self):
        self.create_directory("ui/", "testdir")
        self.objs.append("ui/testdir")
        resp = self.upload_metadata_object(path="ui/testdir")
        self.objs.append("ui/testdir/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("ui/testdir")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        resp, _ =\
            self.delete_metadata_obj_or_folder("ui/testdir/testfile.txt")
        self.assertEqual(resp['status'], '200')
        resp, _ = self.delete_metadata_obj_or_folder("ui/testdir")
        self.assertEqual(resp['status'], '200')
        resp, body = self.get_list_metadata_objects("ui")
        self.assertEqual(resp['status'], '200')
        self.assertNotIn('testfile.txt', body)
        self.objs.pop(self.objs.index("ui/testdir"))
        self.objs.pop(self.objs.index("ui/testdir/testfile.txt"))

    @testtools.skip('Bug https://bugs.launchpad.net/murano/+bug/1249303')
    @attr(type='negative')
    def test_delete_nonempty_folder_in_heat(self):
        self.create_directory("heat/", "testdir")
        self.objs.append("heat/testdir")
        self.upload_metadata_object(path="heat/testdir")
        self.objs.append("heat/testdir/testfile.txt")
        self.assertRaises(Exception, self.delete_metadata_obj_or_folder,
                          "heat/testdir")
        self.delete_metadata_obj_or_folder("heat/testdir/testfile.txt")
        self.delete_metadata_obj_or_folder("heat/testdir")
        self.objs.pop(self.objs.index("heat/testdir"))
        self.objs.pop(self.objs.index("heat/testdir/testfile.txt"))

    @attr(type='positive')
    def test_create_folder_and_upload_file_heat(self):
        self.create_directory("heat/", "testdir")
        self.objs.append("heat/testdir")
        resp = self.upload_metadata_object(path="heat/testdir")
        self.objs.append("heat/testdir/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("heat/testdir")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        resp, _ =\
            self.delete_metadata_obj_or_folder("heat/testdir/testfile.txt")
        self.assertEqual(resp['status'], '200')
        resp, _ = self.delete_metadata_obj_or_folder("heat/testdir")
        self.assertEqual(resp['status'], '200')
        resp, body = self.get_list_metadata_objects("heat")
        self.assertEqual(resp['status'], '200')
        self.assertNotIn('testfile.txt', body)
        self.objs.pop(self.objs.index("heat/testdir"))
        self.objs.pop(self.objs.index("heat/testdir/testfile.txt"))

    @testtools.skip('Bug https://bugs.launchpad.net/murano/+bug/1249303')
    @attr(type='negative')
    def test_delete_nonempty_folder_in_agent(self):
        self.create_directory("agent/", "testdir")
        self.objs.append("agent/testdir")
        self.upload_metadata_object(path="agent/testdir")
        self.objs.append("agent/testdir/testfile.txt")
        self.assertRaises(Exception, self.delete_metadata_obj_or_folder,
                          "agent/testdir")
        self.delete_metadata_obj_or_folder("agent/testdir/testfile.txt")
        self.delete_metadata_obj_or_folder("agent/testdir")
        self.objs.pop(self.objs.index("agent/testdir"))
        self.objs.pop(self.objs.index("agent/testdir/testfile.txt"))

    @attr(type='positive')
    def test_create_folder_and_upload_file_agent(self):
        self.create_directory("agent/", "testdir")
        self.objs.append("agent/testdir")
        resp = self.upload_metadata_object(path="agent/testdir")
        self.objs.append("agent/testdir/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("agent/testdir")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        resp, _ =\
            self.delete_metadata_obj_or_folder("agent/testdir/testfile.txt")
        self.assertEqual(resp['status'], '200')
        resp, _ = self.delete_metadata_obj_or_folder("agent/testdir")
        self.assertEqual(resp['status'], '200')
        resp, body = self.get_list_metadata_objects("agent")
        self.assertEqual(resp['status'], '200')
        self.assertNotIn('testfile.txt', body)
        self.objs.pop(self.objs.index("agent/testdir"))
        self.objs.pop(self.objs.index("agent/testdir/testfile.txt"))

    @testtools.skip('Bug https://bugs.launchpad.net/murano/+bug/1249303')
    @attr(type='negative')
    def test_delete_nonempty_folder_in_scripts(self):
        self.create_directory("scripts/", "testdir")
        self.objs.append("scripts/testdir")
        self.upload_metadata_object(path="scripts/testdir")
        self.objs.append("scripts/testdir/testfile.txt")
        self.assertRaises(Exception, self.delete_metadata_obj_or_folder,
                          "scripts/testdir")
        self.delete_metadata_obj_or_folder("scripts/testdir/testfile.txt")
        self.delete_metadata_obj_or_folder("scripts/testdir")
        self.objs.pop(self.objs.index("scripts/testdir"))
        self.objs.pop(self.objs.index("scripts/testdir/testfile.txt"))

    @attr(type='positive')
    def test_create_folder_and_upload_file_scripts(self):
        self.create_directory("scripts/", "testdir")
        self.objs.append("scripts/testdir")
        resp = self.upload_metadata_object(path="scripts/testdir")
        self.objs.append("scripts/testdir/testfile.txt")
        resp1, body1 = self.get_list_metadata_objects("scripts/testdir")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp1['status'], '200')
        self.assertIn('testfile.txt', body1)
        resp, _ =\
            self.delete_metadata_obj_or_folder("scripts/testdir/testfile.txt")
        self.assertEqual(resp['status'], '200')
        resp, _ = self.delete_metadata_obj_or_folder("scripts/testdir")
        self.assertEqual(resp['status'], '200')
        resp, body = self.get_list_metadata_objects("scripts")
        self.assertEqual(resp['status'], '200')
        self.assertNotIn('testfile.txt', body)
        self.objs.pop(self.objs.index("scripts/testdir"))
        self.objs.pop(self.objs.index("scripts/testdir/testfile.txt"))

    @attr(type='smoke')
    def test_create_and_delete_new_service(self):
        resp, body = self.create_new_service('test')
        self.services.append('test')
        self.assertEqual(resp['status'], '200')
        self.assertIn('success', body)
        resp, body = self.delete_service('test')
        self.assertEqual(resp['status'], '200')
        self.assertIn('success', body)
        self.services.pop(self.services.index('test'))

    @attr(type='smoke')
    def test_update_created_service(self):
        self.create_new_service('test')
        self.services.append('test')
        resp, body = self.update_new_service('test')
        self.assertEqual(resp['status'], '200')
        self.assertIn('success', body)
        self.delete_service('test')
        self.services.pop(self.services.index('test'))

    @attr(type='positive')
    def test_create_complex_service(self):
        resp, body, post_body = self.create_complex_service('test')
        self.services.append('test')
        self.assertEqual(resp['status'], '200')
        self.assertIn('success', body)
        resp, body = self.get_metadata_object('services/test')
        self.delete_service('test')
        self.assertEqual(resp['status'], '200')
        for k in post_body.values():
            if isinstance(k, list):
                for j in k:
                    self.assertIn(j, body)
        self.services.pop(self.services.index('test'))

    @attr(type='smoke')
    def test_get_list_all_services(self):
        resp, body = self.get_list_metadata_objects('services')
        self.assertEqual(resp['status'], '200')
        self.assertIsNotNone(body)

    @attr(type='smoke')
    def test_switch_service_parameter(self):
        self.create_complex_service('test')
        self.services.append('test')
        resp, body = self.switch_service_parameter('test')
        self.assertEqual(resp['status'], '200')
        self.assertEqual(body['result'], 'success')
        self.delete_service('test')
        self.services.pop(self.services.index('test'))

    @testtools.skip('Bug https://bugs.launchpad.net/murano/+bug/1268976')
    @attr(type='negative')
    def test_switch_parameter_none_existing_service(self):
        self.assertRaises(exceptions.NotFound, self.switch_service_parameter,
                          'hupj')

    @attr(type='positive')
    def test_reset_cache(self):
        resp, body = self.reset_cache()
        self.assertEqual(resp['status'], '200')
        self.assertEqual(body['result'], 'success')

    @attr(type='smoke')
    def test_get_meta_info_about_service(self):
        self.create_new_service('test')
        self.services.append('test')
        resp, body = self.get_list_of_meta_information_about_service('test')
        self.delete_service('test')
        self.assertEqual(resp['status'], '200')
        self.assertEqual(body['name'], 'test')
        self.assertEqual(body['version'], '0.1')
        self.services.pop(self.services.index('test'))

    @attr(type='negative')
    def test_get_meta_info_about_nonexistent_service(self):
        self.assertRaises(exceptions.NotFound,
                          self.get_list_of_meta_information_about_service,
                          "hupj")
