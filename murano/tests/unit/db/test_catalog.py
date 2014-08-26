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

import uuid

from oslo.db import exception as db_exception
from webob import exc

from murano.db.catalog import api
from murano.tests.unit import base
from murano.tests.unit import utils


class CatalogDBTestCase(base.MuranoWithDBTestCase):

    def setUp(self):
        super(CatalogDBTestCase, self).setUp()
        self.tenant_id = str(uuid.uuid4())
        self.context = utils.dummy_context(tenant_id=self.tenant_id)

    def _create_categories(self):
        api.category_add('cat1')
        api.category_add('cat2')

    def _stub_package(self):
        return {
            'archive': "archive blob here",
            'fully_qualified_name': 'com.example.package',
            'type': 'class',
            'author': 'OpenStack',
            'name': 'package',
            'enabled': True,
            'description': 'some text',
            'is_public': False,
            'tags': ['tag1', 'tag2'],
            'logo': "logo blob here",
            'ui_definition': '{}',
        }

    def test_list_empty_categories(self):
        res = api.category_get_names()
        self.assertEqual(0, len(res))

    def test_add_list_categories(self):
        self._create_categories()

        res = api.categories_list()
        self.assertEqual(2, len(res))

        for cat in res:
            self.assertTrue(cat.id is not None)
            self.assertTrue(cat.name.startswith('cat'))

    def test_package_upload(self):
        self._create_categories()
        values = self._stub_package()

        package = api.package_upload(values, self.tenant_id)

        self.assertIsNotNone(package.id)
        for k in values.keys():
            self.assertEqual(values[k], package[k])

    def test_package_fqn_is_unique(self):
        self._create_categories()
        values = self._stub_package()

        api.package_upload(values, self.tenant_id)
        self.assertRaises(db_exception.DBDuplicateEntry,
                          api.package_upload, values, self.tenant_id)

    def test_package_delete(self):
        values = self._stub_package()
        package = api.package_upload(values, self.tenant_id)

        api.package_delete(package.id, self.context)

        self.assertRaises(exc.HTTPNotFound,
                          api.package_get, package.id, self.context)
