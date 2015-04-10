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

import cgi
import cStringIO
import imghdr
import json
import os

import mock
from oslo.utils import timeutils

from murano.api.v1 import catalog
from murano.common import policy
from murano.db.catalog import api as db_catalog_api
from murano.db import models
from murano.packages import load_utils
import murano.tests.unit.api.base as test_base
import murano.tests.unit.utils as test_utils


class TestCatalogApi(test_base.ControllerTest, test_base.MuranoApiTestCase):
    def setUp(self):
        super(TestCatalogApi, self).setUp()
        self.controller = catalog.Controller()

    def _test_package(self):
        package_dir = os.path.abspath(
            os.path.join(
                __file__,
                '../../../packages/test_packages/test.mpl.v1.app'
            )
        )
        pkg = load_utils.load_from_dir(
            package_dir
        )
        package = {
            'fully_qualified_name': pkg.full_name,
            'type': pkg.package_type,
            'author': pkg.author,
            'supplier': pkg.supplier,
            'name': pkg.display_name,
            'description': pkg.description,
            'is_public': True,
            'tags': pkg.tags,
            'logo': pkg.logo,
            'supplier_logo': pkg.supplier_logo,
            'ui_definition': pkg.raw_ui,
            'class_definitions': pkg.classes,
            'archive': pkg.blob,
            'categories': [],
        }
        return pkg, package

    def test_load_package_with_supplier_info(self):
        self._set_policy_rules(
            {'get_package': '@'}
        )
        package_from_dir, package = self._test_package()

        saved_package = db_catalog_api.package_upload(package, '')

        self.expect_policy_check('get_package',
                                 {'package_id': saved_package.id})

        req = self._get('/v1/catalog/packages/%s' % saved_package.id)
        result = self.controller.get(req, saved_package.id)

        self.assertEqual(package['supplier'], result['supplier'])

        req = self._get(
            '/v1/catalog/packages/%s/supplier_logo' % saved_package.id
        )
        result = self.controller.get_supplier_logo(req, saved_package.id)

        self.assertEqual(imghdr.what('', result), 'png')

    def test_add_public_unauthorized(self):
        policy.set_rules({
            'upload_package': '@',
            'publicize_package': 'is_admin:True',
            'delete_package': 'is_admin:True',
        })

        self.expect_policy_check('upload_package')
        self.expect_policy_check('delete_package', mock.ANY)
        self.expect_policy_check('upload_package')
        self.expect_policy_check('publicize_package')
        self.expect_policy_check('upload_package')
        self.expect_policy_check('publicize_package')

        file_obj_str = cStringIO.StringIO("This is some dummy data")
        file_obj = mock.MagicMock(cgi.FieldStorage)
        file_obj.file = file_obj_str
        package_from_dir, package_metadata = self._test_package()

        body = '''\

--BOUNDARY
Content-Disposition: form-data; name="__metadata__"

{0}
--BOUNDARY
Content-Disposition: form-data; name="ziparchive"; filename="file.zip"

This is a fake zip archive
--BOUNDARY--'''

        with mock.patch('murano.packages.load_utils.load_from_file') as lff:
            lff.return_value = package_from_dir

            # Uploading a non-public package
            req = self._post(
                '/catalog/packages',
                body.format(json.dumps({'is_public': False})),
                content_type='multipart/form-data; ; boundary=BOUNDARY',
            )
            res = req.get_response(self.api)
            self.assertEqual(200, res.status_code)

            self.is_admin = True
            app_id = json.loads(res.body)['id']
            req = self._delete('/catalog/packages/{0}'.format(app_id))
            res = req.get_response(self.api)

            self.is_admin = False
            # Uploading a public package fails
            req = self._post(
                '/catalog/packages',
                body.format(json.dumps({'is_public': True})),
                content_type='multipart/form-data; ; boundary=BOUNDARY',
            )
            res = req.get_response(self.api)
            self.assertEqual(403, res.status_code)

            # Uploading a public package passes for admin
            self.is_admin = True
            req = self._post(
                '/catalog/packages',
                body.format(json.dumps({'is_public': True})),
                content_type='multipart/form-data; ; boundary=BOUNDARY',
            )
            res = req.get_response(self.api)
            self.assertEqual(200, res.status_code)

    def test_add_category(self):
        """Check that category added successfully
        """

        self._set_policy_rules({'add_category': '@'})
        self.expect_policy_check('add_category')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        expected = {
            'name': 'new_category',
            'created': timeutils.isotime(fake_now)[:-1],
            'updated': timeutils.isotime(fake_now)[:-1],
            'package_count': 0,
        }

        body = {'name': 'new_category'}
        req = self._post('/catalog/categories', json.dumps(body))
        result = req.get_response(self.api)
        processed_result = json.loads(result.body)
        self.assertIn('id', processed_result.keys())
        expected['id'] = processed_result['id']
        self.assertDictEqual(expected, processed_result)

    def test_delete_category(self):
        """Check that category deleted successfully
        """

        self._set_policy_rules({'delete_category': '@'})
        self.expect_policy_check('delete_category',
                                 {'category_id': '12345'})

        fake_now = timeutils.utcnow()
        expected = {'name': 'new_category',
                    'created': fake_now,
                    'updated': fake_now,
                    'id': '12345'}

        e = models.Category(**expected)
        test_utils.save_models(e)

        req = self._delete('/catalog/categories/12345')
        processed_result = req.get_response(self.api)
        self.assertEqual('', processed_result.body)
        self.assertEqual(200, processed_result.status_code)

    def test_add_category_failed_for_non_admin(self):
        """Check that non admin user couldn't add new category
        """

        self._set_policy_rules({'add_category': 'role:context_admin'})
        self.is_admin = False
        self.expect_policy_check('add_category')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        body = {'name': 'new_category'}
        req = self._post('/catalog/categories', json.dumps(body))
        result = req.get_response(self.api)
        self.assertEqual(403, result.status_code)
