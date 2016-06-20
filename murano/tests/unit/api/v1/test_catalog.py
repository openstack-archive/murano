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
import imghdr
import os
import uuid

import mock
from oslo_serialization import jsonutils
from oslo_utils import timeutils
import six
from six.moves import cStringIO
from six.moves import range

from murano.api.v1 import catalog
from murano.db.catalog import api as db_catalog_api
from murano.db import models
from murano.packages import exceptions
from murano.packages import load_utils
import murano.tests.unit.api.base as test_base
import murano.tests.unit.utils as test_utils


class TestCatalogApi(test_base.ControllerTest, test_base.MuranoApiTestCase):

    def setUp(self):
        super(TestCatalogApi, self).setUp()
        self.controller = catalog.Controller()
        _, self.test_package = self._test_package()

    def _add_pkg(self, tenant_name, public=False, classes=None, **kwargs):
        package_to_upload = self.test_package.copy()
        package_to_upload['is_public'] = public
        package_to_upload['fully_qualified_name'] = str(uuid.uuid4())
        if classes:
            package_to_upload['class_definitions'] = classes
        else:
            package_to_upload['class_definitions'] = []
        package_to_upload.update(kwargs)
        return db_catalog_api.package_upload(
            package_to_upload, tenant_name)

    def test_packages_filtering_admin(self):
        self.is_admin = True
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        for dummy in range(7):
            self.expect_policy_check('get_package')
            self.expect_policy_check('manage_public_package')

        pkg = self._add_pkg('test_tenant', type='Library')
        self._add_pkg('test_tenant')
        self._add_pkg('test_tenant2', public=True, type='Library')
        self._add_pkg('test_tenant3')

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'False',
                                             'owned': 'False'}))
        self.assertEqual(4, len(result['packages']))
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'False',
                                             'owned': 'True'}))
        self.assertEqual(2, len(result['packages']))

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True',
                                             'owned': 'False'}))
        self.assertEqual(3, len(result['packages']))
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True',
                                             'owned': 'True'}))
        self.assertEqual(2, len(result['packages']))

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={
                'owned': 'True',
                'fqn': pkg.fully_qualified_name}))
        self.assertEqual(1, len(result['packages']))
        self.assertEqual(pkg.fully_qualified_name,
                         result['packages'][0]['fully_qualified_name'])

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={
                'owned': 'True',
                'type': 'Library'}))
        self.assertEqual(1, len(result['packages']))
        self.assertEqual(pkg.fully_qualified_name,
                         result['packages'][0]['fully_qualified_name'])

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={
                'type': 'Library'}))
        self.assertEqual(2, len(result['packages']))

    def test_packages_filtering_non_admin(self):
        self.is_admin = False
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        for dummy in range(8):
            self.expect_policy_check('get_package')
            self.expect_policy_check('manage_public_package')

        pkg = self._add_pkg('test_tenant', type='Library')
        self._add_pkg('test_tenant')
        self._add_pkg('test_tenant2', public=True, type='Library')
        self._add_pkg('test_tenant3')

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'False',
                                             'owned': 'False'}))
        self.assertEqual(3, len(result['packages']))
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'False',
                                             'owned': 'True'}))
        self.assertEqual(2, len(result['packages']))
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True',
                                             'owned': 'False'}))
        self.assertEqual(3, len(result['packages']))
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True',
                                             'owned': 'True'}))
        self.assertEqual(2, len(result['packages']))

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={
                'owned': 'True',
                'fqn': pkg.fully_qualified_name}))
        self.assertEqual(1, len(result['packages']))
        self.assertEqual(pkg.fully_qualified_name,
                         result['packages'][0]['fully_qualified_name'])

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={
                'owned': 'True',
                'type': 'Library'}))
        self.assertEqual(1, len(result['packages']))
        self.assertEqual(pkg.fully_qualified_name,
                         result['packages'][0]['fully_qualified_name'])

        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={
                'type': 'Library'}))
        self.assertEqual(2, len(result['packages']))

        self._set_policy_rules({'get_package': '',
                                'manage_public_package': '!'})
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'False'}))
        self.assertEqual(2, len(result['packages']))

    def test_packages_filter_by_id(self):
        """Test that packages are filtered by ID

        GET /catalog/packages with parameter "id" returns packages
        filtered by id.
        """
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        _, package1_data = self._test_package()
        _, package2_data = self._test_package()

        package1_data['fully_qualified_name'] += '_1'
        package1_data['name'] += '_1'
        package1_data['class_definitions'] = (u'test.mpl.v1.app.Thing1',)
        package2_data['fully_qualified_name'] += '_2'
        package2_data['name'] += '_2'
        package2_data['class_definitions'] = (u'test.mpl.v1.app.Thing2',)

        expected_package = db_catalog_api.package_upload(package1_data, '')
        db_catalog_api.package_upload(package2_data, '')

        req = self._get('/catalog/packages',
                        params={'id': expected_package.id})
        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        res = req.get_response(self.api)
        self.assertEqual(200, res.status_code)

        self.assertEqual(1, len(res.json['packages']))

        found_package = res.json['packages'][0]

        self.assertEqual(expected_package.id, found_package['id'])

    def test_packages_filter_by_name(self):
        """Test that packages are filtered by name

        GET /catalog/packages with parameter "name" returns packages
        filtered by name.
        """
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )

        expected_pkg1 = self._add_pkg("test_tenant", name="test_pkgname_1")
        expected_pkg2 = self._add_pkg("test_tenant", name="test_pkgname_2")

        req_pkgname1 = self._get('/catalog/packages',
                                 params={'name': expected_pkg1.name})
        req_pkgname2 = self._get('/catalog/packages',
                                 params={'name': expected_pkg2.name})

        for dummy in range(2):
            self.expect_policy_check('get_package')
            self.expect_policy_check('manage_public_package')

        res_pkgname1 = req_pkgname1.get_response(self.api)
        self.assertEqual(200, res_pkgname1.status_code)
        self.assertEqual(1, len(res_pkgname1.json['packages']))
        self.assertEqual(expected_pkg1.name,
                         res_pkgname1.json['packages'][0]['name'])

        res_pkgname2 = req_pkgname2.get_response(self.api)
        self.assertEqual(200, res_pkgname2.status_code)
        self.assertEqual(1, len(res_pkgname2.json['packages']))
        self.assertEqual(expected_pkg2.name,
                         res_pkgname2.json['packages'][0]['name'])

    def test_packages_filter_by_type(self):
        """Test that packages are filtered by type

        GET /catalog/packages with parameter "type" returns packages
        filtered by type.
        """
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        excepted_pkg1 = self._add_pkg("test_tenant", type='Library')
        excepted_pkg2 = self._add_pkg("test_tenant", type='Library')
        excepted_pkg3 = self._add_pkg("test_tenant", type='Application')

        # filter by type=Library can see 2 pkgs
        req_lib = self._get('/catalog/packages',
                            params={'type': 'Library'})

        # filter by type=Application only see 1 pkgs
        req_app = self._get('/catalog/packages',
                            params={'type': 'Application'})

        for dummy in range(2):
            self.expect_policy_check('get_package')
            self.expect_policy_check('manage_public_package')

        res_lib = req_lib.get_response(self.api)

        self.assertEqual(200, res_lib.status_code)
        self.assertEqual(2, len(res_lib.json['packages']))

        self.assertEqual('Library', res_lib.json['packages'][0]['type'])
        self.assertEqual(excepted_pkg1.name,
                         res_lib.json['packages'][0]['name'])

        self.assertEqual('Library', res_lib.json['packages'][1]['type'])
        self.assertEqual(excepted_pkg2.name,
                         res_lib.json['packages'][1]['name'])

        res_app = req_app.get_response(self.api)

        self.assertEqual(200, res_app.status_code)
        self.assertEqual(1, len(res_app.json['packages']))

        self.assertEqual('Application', res_app.json['packages'][0]['type'])
        self.assertEqual(excepted_pkg3.name,
                         res_app.json['packages'][0]['name'])

    def test_packages(self):
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        for dummy in range(9):
            self.expect_policy_check('get_package')
            self.expect_policy_check('manage_public_package')
        result = self.controller.search(self._get('/v1/catalog/packages/'))
        self.assertEqual(0, len(result['packages']))

        self._add_pkg('test_tenant')
        self._add_pkg('test_tenant')
        self._add_pkg('other_tenant')
        self._add_pkg('other_tenant')

        # non-admin should only see 2 pkgs he can edit.
        self.is_admin = False
        result = self.controller.search(self._get('/v1/catalog/packages/'))
        self.assertEqual(2, len(result['packages']))
        # can only deploy his + public
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True'}))
        self.assertEqual(2, len(result['packages']))

        # admin can edit anything
        self.is_admin = True
        result = self.controller.search(self._get('/v1/catalog/packages/'))
        self.assertEqual(4, len(result['packages']))
        # admin can only deploy his + public
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True'}))
        self.assertEqual(2, len(result['packages']))

        self._add_pkg('test_tenant', public=True)
        self._add_pkg('other_tenant', public=True)

        # non-admin are allowed to edit public packages by policy
        self.is_admin = False
        result = self.controller.search(self._get('/v1/catalog/packages/'))
        self.assertEqual(4, len(result['packages']))
        # can deploy mine + other public
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True'}))
        self.assertEqual(4, len(result['packages']))

        # admin can edit anything
        self.is_admin = True
        result = self.controller.search(self._get('/v1/catalog/packages/'))
        self.assertEqual(6, len(result['packages']))
        # can deploy mine + public
        result = self.controller.search(self._get(
            '/v1/catalog/packages/', params={'catalog': 'True'}))
        self.assertEqual(4, len(result['packages']))

    def _test_package(self, manifest='manifest.yaml'):
        package_dir = os.path.abspath(
            os.path.join(
                __file__,
                '../../../packages/test_packages/test.mpl.v1.app',
            )
        )
        pkg = load_utils.load_from_dir(
            package_dir, filename=manifest
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
            'ui_definition': pkg.ui,
            'class_definitions': tuple(pkg.classes),
            'archive': pkg.blob,
            'categories': [],
        }
        return pkg, package

    def test_not_valid_logo(self):
        self.assertRaises(exceptions.PackageLoadError,
                          self._test_package, 'manifest_with_broken_logo.yaml')

    def test_load_package_with_supplier_info(self):
        self._set_policy_rules(
            {'get_package': '@'}
        )
        _, package = self._test_package()

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

        self.assertEqual('png', imghdr.what('', result))

    def test_download_package(self):
        self._set_policy_rules(
            {'download_package': '@'}
        )
        _, package = self._test_package()

        saved_package = db_catalog_api.package_upload(package, '')

        self.expect_policy_check('download_package',
                                 {'package_id': saved_package.id})

        req = self._get_with_accept('/catalog/packages/%s/download'
                                    % saved_package.id,
                                    accept='application/octet-stream')

        result = req.get_response(self.api)

        self.assertEqual(200, result.status_code)

    def test_download_package_negative(self):

        _, package = self._test_package()

        saved_package = db_catalog_api.package_upload(package, '')

        req = self._get_with_accept('/catalog/packages/%s/download'
                                    % saved_package.id,
                                    accept='application/foo')

        result = req.get_response(self.api)

        self.assertEqual(406, result.status_code)
        self.assertTrue(b'Acceptable response can not be provided'
                        in result.body)

    def test_get_ui_definition(self):
        self._set_policy_rules(
            {'get_package': '@'}
        )
        _, package = self._test_package()

        saved_package = db_catalog_api.package_upload(package, '')

        self.expect_policy_check('get_package',
                                 {'package_id': saved_package.id})

        req = self._get_with_accept('/catalog/packages/%s/ui'
                                    % saved_package.id,
                                    accept="text/plain")

        result = req.get_response(self.api)

        self.assertEqual(200, result.status_code)

    def test_get_ui_definition_negative(self):
        _, package = self._test_package()

        saved_package = db_catalog_api.package_upload(package, '')

        req = self._get_with_accept('/catalog/packages/%s/ui'
                                    % saved_package.id,
                                    accept='application/foo')

        result = req.get_response(self.api)

        self.assertEqual(406, result.status_code)
        self.assertTrue(b'Acceptable response can not be provided'
                        in result.body)

    def test_get_logo(self):
        self._set_policy_rules(
            {'get_package': '@'}
        )
        _, package = self._test_package()

        saved_package = db_catalog_api.package_upload(package, '')

        self.expect_policy_check('get_package',
                                 {'package_id': saved_package.id})

        req = self._get_with_accept('/catalog/packages/%s/logo'
                                    % saved_package.id,
                                    accept="application/octet-stream")

        result = req.get_response(self.api)

        self.assertEqual(200, result.status_code)
        self.assertEqual(package['logo'], result.body)

    def test_get_logo_negative(self):
        _, package = self._test_package()

        saved_package = db_catalog_api.package_upload(package, '')

        req = self._get_with_accept('/catalog/packages/%s/logo'
                                    % saved_package.id,
                                    accept='application/foo')

        result = req.get_response(self.api)

        self.assertEqual(406, result.status_code)
        self.assertTrue(b'Acceptable response can not be provided'
                        in result.body)

    def test_add_public_unauthorized(self):
        self._set_policy_rules({
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

        file_obj_str = cStringIO("This is some dummy data")
        file_obj = mock.MagicMock(cgi.FieldStorage)
        file_obj.file = file_obj_str
        package_from_dir, _ = self._test_package()

        body_fmt = '''\

--BOUNDARY
Content-Disposition: form-data; name="__metadata__"

{0}
--BOUNDARY
Content-Disposition: form-data; name="ziparchive"; filename="file.zip"

This is a fake zip archive
--BOUNDARY--'''

        def format_body(content):
            content = jsonutils.dumps(content)
            body = body_fmt.format(content)
            if six.PY3:
                body = body.encode('utf-8')
            return body

        with mock.patch('murano.packages.load_utils.load_from_file') as lff:
            ctxmgr = mock.Mock()
            ctxmgr.__enter__ = mock.Mock(return_value=package_from_dir)
            ctxmgr.__exit__ = mock.Mock(return_value=False)
            lff.return_value = ctxmgr

            # Uploading a non-public package
            req = self._post(
                '/catalog/packages',
                format_body({'is_public': False}),
                content_type='multipart/form-data; ; boundary=BOUNDARY',
            )
            res = req.get_response(self.api)
            self.assertEqual(200, res.status_code)

            self.is_admin = True
            app_id = jsonutils.loads(res.body)['id']
            req = self._delete('/catalog/packages/{0}'.format(app_id))
            res = req.get_response(self.api)

            self.is_admin = False
            # Uploading a public package fails
            req = self._post(
                '/catalog/packages',
                format_body({'is_public': True}),
                content_type='multipart/form-data; ; boundary=BOUNDARY',
            )
            res = req.get_response(self.api)
            self.assertEqual(403, res.status_code)

            # Uploading a public package passes for admin
            self.is_admin = True
            req = self._post(
                '/catalog/packages',
                format_body({'is_public': True}),
                content_type='multipart/form-data; ; boundary=BOUNDARY',
            )
            res = req.get_response(self.api)
            self.assertEqual(200, res.status_code)

    def test_add_category(self):
        """Check that category added successfully"""

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
        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        processed_result = jsonutils.loads(result.body)
        self.assertIn('id', processed_result.keys())
        expected['id'] = processed_result['id']
        self.assertDictEqual(expected, processed_result)

    def test_delete_category(self):
        """Check that category deleted successfully"""

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
        self.assertEqual(b'', processed_result.body)
        self.assertEqual(200, processed_result.status_code)

    def test_add_category_failed_for_non_admin(self):
        """Check that non admin user couldn't add new category"""

        self._set_policy_rules({'add_category': 'role:context_admin'})
        self.is_admin = False
        self.expect_policy_check('add_category')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        body = {'name': 'new_category'}
        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(403, result.status_code)

    def test_add_long_category(self):
        """Test that category name does not exceed 80 characters

        Check that a category that contains more then 80 characters
        fails to be added
        """

        self._set_policy_rules({'add_category': '@'})
        self.expect_policy_check('add_category')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        body = {'name': 'cat' * 80}
        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)
        result_message = result.text.replace('\n', '')
        self.assertIn('Category name should be 80 characters maximum',
                      result_message)

    def test_list_category(self):
        names = ['cat1', 'cat2']
        for name in names:
            db_catalog_api.category_add(name)

        self._set_policy_rules({'get_category': '@'})
        self.expect_policy_check('get_category')

        req = self._get('/catalog/categories')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        result_categories = jsonutils.loads(result.body)['categories']
        self.assertEqual(2, len(result_categories))
        self.assertEqual(names, [c['name'] for c in result_categories])

        params = {'sort_keys': 'created,  id'}
        req = self._get('/catalog/categories', params)
        self.expect_policy_check('get_category')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        result_categories = jsonutils.loads(result.body)['categories']
        self.assertEqual(names, [c['name'] for c in result_categories])

        names.reverse()

        params = {'sort_dir': 'desc'}
        req = self._get('/catalog/categories', params)
        self.expect_policy_check('get_category')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        result_categories = jsonutils.loads(result.body)['categories']
        self.assertEqual(names, [c['name'] for c in result_categories])

    def test_list_category_negative(self):
        self._set_policy_rules({'get_category': '@'})
        self.expect_policy_check('get_category')

        req = self._get('/catalog/categories', {'sort_dir': 'test'})
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)

        self.expect_policy_check('get_category')
        req = self._get('/catalog/categories', {'sort_keys': 'test'})
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)

        self.expect_policy_check('get_category')
        req = self._get('/catalog/categories', {'test': ['test']})
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)
