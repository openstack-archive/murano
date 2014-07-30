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

import imghdr
import mock
from murano.api.v1 import catalog
from murano.common import policy
from murano.db.catalog import api as db_catalog_api
from murano.packages import load_utils
import murano.tests.unit.api.base as test_base
import os


@mock.patch.object(policy, 'check')
class TestCatalogApi(test_base.ControllerTest, test_base.MuranoApiTestCase):
    def setUp(self):
        super(TestCatalogApi, self).setUp()
        self.controller = catalog.Controller()

    def test_load_package_with_supplier_info(self, mock_policy_check):
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

        saved_package = db_catalog_api.package_upload(package, '')

        req = self._get('/v1/catalog/packages/%s' % saved_package.id)
        result = self.controller.get(req, saved_package.id)

        self.assertEqual(package['supplier'], result['supplier'])

        req = self._get(
            '/v1/catalog/packages/%s/supplier_logo' % saved_package.id
        )
        result = self.controller.get_supplier_logo(req, saved_package.id)

        self.assertEqual(imghdr.what('', result), 'png')
