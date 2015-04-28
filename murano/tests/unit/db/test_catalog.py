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
        self.tenant_id_2 = str(uuid.uuid4())
        self.context = utils.dummy_context(tenant_id=self.tenant_id)
        self.context_2 = utils.dummy_context(tenant_id=self.tenant_id_2)

        self.context_admin = utils.dummy_context(tenant_id=self.tenant_id)
        self.context_admin.is_admin = True

    def _create_categories(self):
        api.category_add('cat1')
        api.category_add('cat2')

    def _stub_package(self, **kwargs):
        base = {
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
        base.update(**kwargs)
        return base

    def get_change(self, op, path, value):
        return {
            'op': op,
            'path': path,
            'value': value
        }

    def test_package_search_search(self):
        pkg1 = api.package_upload(
            self._stub_package(
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)
        pkg2 = api.package_upload(
            self._stub_package(
                tags=[],
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)

        res = api.package_search(
            {'search': 'tag1'}, self.context)
        self.assertEqual(len(res), 1)
        res = api.package_search(
            {'search': pkg1.fully_qualified_name}, self.context)
        self.assertEqual(len(res), 1)
        res = api.package_search(
            {'search': pkg2.fully_qualified_name}, self.context)
        self.assertEqual(len(res), 1)
        res = api.package_search(
            {'search': 'not_a_valid_uuid'}, self.context)
        self.assertEqual(len(res), 0)

        res = api.package_search(
            {'search': 'some text'}, self.context)
        self.assertEqual(len(res), 2)

    def test_package_search_tags(self):
        api.package_upload(
            self._stub_package(
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)
        api.package_upload(
            self._stub_package(
                tags=[],
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)

        res = api.package_search(
            {'tag': ['tag1']}, self.context)
        self.assertEqual(len(res), 1)
        res = api.package_search(
            {'tag': ['tag2']}, self.context)
        self.assertEqual(len(res), 1)
        res = api.package_search(
            {'tag': ['tag3']}, self.context)
        self.assertEqual(len(res), 0)

    def test_package_search_type(self):
        api.package_upload(
            self._stub_package(
                type="Application",
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)
        api.package_upload(
            self._stub_package(
                type="Library",
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)

        res = api.package_search(
            {'type': 'Library'}, self.context)
        self.assertEqual(len(res), 1)
        res = api.package_search(
            {'type': 'Application'}, self.context)
        self.assertEqual(len(res), 1)

    def test_package_search_disabled(self):
        api.package_upload(
            self._stub_package(
                is_public=True,
                enabled=True,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)
        api.package_upload(
            self._stub_package(
                is_public=True,
                enabled=False,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)

        res = api.package_search(
            {'include_disabled': 'false'}, self.context)
        self.assertEqual(len(res), 1)
        res = api.package_search(
            {'include_disabled': 'true'}, self.context)
        self.assertEqual(len(res), 2)

    def test_package_search_owned(self):
        api.package_upload(
            self._stub_package(
                is_public=True,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)
        api.package_upload(
            self._stub_package(
                is_public=True,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id_2)

        res = api.package_search({'owned': 'true'}, self.context_admin)
        self.assertEqual(len(res), 1)
        res = api.package_search({'owned': 'false'}, self.context_admin)
        self.assertEqual(len(res), 2)

    def test_package_search_no_filters_catalog(self):
        res = api.package_search({}, self.context, catalog=True)
        self.assertEqual(len(res), 0)

        api.package_upload(
            self._stub_package(
                is_public=True,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)
        api.package_upload(
            self._stub_package(
                is_public=False,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)

        api.package_upload(
            self._stub_package(
                is_public=True,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id_2)
        api.package_upload(
            self._stub_package(
                is_public=False,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id_2)

        # catalog=True should show public + mine
        res = api.package_search({}, self.context, catalog=True)
        self.assertEqual(len(res), 3)

        res = api.package_search({}, self.context_admin, catalog=True)
        self.assertEqual(len(res), 3)

    def test_package_search_no_filters(self):
        res = api.package_search({}, self.context)
        self.assertEqual(len(res), 0)

        api.package_upload(
            self._stub_package(
                is_public=True,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)
        api.package_upload(
            self._stub_package(
                is_public=False,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id)

        api.package_upload(
            self._stub_package(
                is_public=True,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id_2)
        api.package_upload(
            self._stub_package(
                is_public=False,
                fully_qualified_name=str(uuid.uuid4())), self.tenant_id_2)

        # I can only edit mine pkgs
        res = api.package_search({}, self.context)
        self.assertEqual(len(res), 2)
        for pkg in res:
            self.assertEqual(pkg.owner_id, self.tenant_id)

        # Admin can see everything
        res = api.package_search({}, self.context_admin)
        self.assertEqual(len(res), 4)

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

    def test_package_upload_to_different_tenants_with_same_fqn(self):
        values = self._stub_package()

        api.package_upload(values, self.tenant_id)
        api.package_upload(values, self.tenant_id_2)

    def test_package_upload_public_public_fqn_violation(self):
        values = self._stub_package(is_public=True)
        api.package_upload(values, self.tenant_id)
        values = self._stub_package(is_public=True)
        self.assertRaises(exc.HTTPConflict, api.package_upload,
                          values, self.tenant_id_2)

    def test_package_upload_public_private_no_fqn_violation(self):
        values = self._stub_package(is_public=True)
        api.package_upload(values, self.tenant_id)
        values = self._stub_package(is_public=False)
        api.package_upload(values, self.tenant_id_2)

    def test_package_upload_private_public_no_fqn_violation(self):
        values = self._stub_package()
        api.package_upload(values, self.tenant_id)
        values = self._stub_package(is_public=True)
        api.package_upload(values, self.tenant_id_2)

    def test_class_name_is_unique(self):
        value = self._stub_package(class_definitions=('foo', 'bar'))
        api.package_upload(value, self.tenant_id)
        value = self._stub_package(class_definitions=('bar', 'baz'),
                                   fully_qualified_name='com.example.package2')
        self.assertRaises(exc.HTTPConflict, api.package_upload, value,
                          self.tenant_id)

    def test_class_name_uniqueness_not_enforced_in_different_tenants(self):
        value = self._stub_package(class_definitions=('foo', 'bar'))
        api.package_upload(value, self.tenant_id)
        value = self._stub_package(class_definitions=('foo', 'bar'),
                                   fully_qualified_name='com.example.package2')
        api.package_upload(value, self.tenant_id_2)

    def test_class_name_public_public_violation(self):
        value = self._stub_package(class_definitions=('foo', 'bar'),
                                   is_public=True)
        api.package_upload(value, self.tenant_id)
        value = self._stub_package(class_definitions=('foo', 'bar'),
                                   is_public=True,
                                   fully_qualified_name='com.example.package2')
        self.assertRaises(exc.HTTPConflict, api.package_upload,
                          value, self.tenant_id_2)

    def test_class_name_public_private_no_violation(self):
        value = self._stub_package(class_definitions=('foo', 'bar'),
                                   is_public=True)
        api.package_upload(value, self.tenant_id)
        value = self._stub_package(class_definitions=('foo', 'bar'),
                                   is_public=False,
                                   fully_qualified_name='com.example.package2')
        api.package_upload(value, self.tenant_id_2)

    def test_class_name_private_public_no_violation(self):
        value = self._stub_package(class_definitions=('foo', 'bar'),
                                   is_public=False)
        api.package_upload(value, self.tenant_id)
        value = self._stub_package(class_definitions=('foo', 'bar'),
                                   is_public=True,
                                   fully_qualified_name='com.example.package2')
        api.package_upload(value, self.tenant_id_2)

    def test_package_make_public(self):
        id = api.package_upload(self._stub_package(), self.tenant_id).id
        patch = self.get_change('replace', ['is_public'], True)
        api.package_update(id, [patch], self.context)
        package = api.package_get(id, self.context)
        self.assertEqual(True, package.is_public)

    def test_package_update_public_public_fqn_violation(self):
        id1 = api.package_upload(self._stub_package(), self.tenant_id).id
        id2 = api.package_upload(self._stub_package(), self.tenant_id_2).id
        patch = self.get_change('replace', ['is_public'], True)
        api.package_update(id1, [patch], self.context)
        self.assertRaises(exc.HTTPConflict, api.package_update,
                          id2, [patch], self.context_2)

    def test_package_update_public_public_class_name_violation(self):
        id1 = api.package_upload(self._stub_package(
            class_definitions=('foo', 'bar')), self.tenant_id).id
        id2 = api.package_upload(self._stub_package(
            class_definitions=('foo', 'bar'),
            fully_qualified_name='com.example.package2'), self.tenant_id_2).id
        patch = self.get_change('replace', ['is_public'], True)
        api.package_update(id1, [patch], self.context)
        self.assertRaises(exc.HTTPConflict, api.package_update,
                          id2, [patch], self.context_2)
