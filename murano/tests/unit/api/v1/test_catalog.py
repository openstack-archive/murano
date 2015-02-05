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
import os

import mock

from murano.api.v1 import catalog
from murano.common import policy
from murano.db.catalog import api as db_catalog_api
from murano.packages import load_utils
import murano.tests.unit.api.base as test_base


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
            'categories': []
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
            'publicize_package': 'role:is_admin or is_admin:True'
        })

        self.expect_policy_check('upload_package')
        self.expect_policy_check('publicize_image')
        self.expect_policy_check('upload_package')
        self.expect_policy_check('publicize_image')

        file_obj_str = cStringIO.StringIO("This is some dummy data")
        file_obj = mock.MagicMock(cgi.FieldStorage)
        file_obj.file = file_obj_str
        package_from_dir, package_metadata = self._test_package()

        body = '''\

--BOUNDARY
Content-Disposition: form-data; name="ziparchive"
Content-Type: text/plain:

This is a fake zip archive
--BOUNDARY
Content-Disposition: form-data; name="metadata"; filename="test.json"
Content-Type: application/json

%s
--BOUNDARY--''' % package_metadata

        with mock.patch('murano.packages.load_utils.load_from_file') as lff:
            lff.return_value = package_from_dir
            req = self._post(
                '/catalog/packages',
                body,
                content_type='multipart/form-data; ; boundary=BOUNDARY',
                params={"is_public": "true"})
            res = req.get_response(self.api)

            # Nobody has access to upload public images
            self.assertEqual(403, res.status_code)

            self.is_admin = True
            req = self._post(
                '/catalog/packages',
                body,
                content_type='multipart/form-data; ; boundary=BOUNDARY',
                params={"is_public": "true"})
            res = req.get_response(self.api)
