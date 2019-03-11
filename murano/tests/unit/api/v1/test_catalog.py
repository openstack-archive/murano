# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.

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
from datetime import datetime
import imghdr
import os
import tempfile
import uuid

import mock
from oslo_config import cfg
from oslo_serialization import jsonutils
from oslo_utils import timeutils
import six
from six.moves import cStringIO
from six.moves import range
from webob import exc

from murano.api.v1 import catalog
from murano.api.v1 import PKG_PARAMS_MAP
from murano.common import exceptions as common_exc
from murano.db.catalog import api as db_catalog_api
from murano.db import models
from murano.packages import exceptions
from murano.packages import load_utils
import murano.tests.unit.api.base as test_base
import murano.tests.unit.utils as test_utils

CONF = cfg.CONF


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

    def test_packages_filter_by_in_category(self):
        """Test that packages are filtered by in:cat1,cat2,cat3

        GET /catalog/packages with parameter "category=in:cat1,cat2,cat3"
        returns packages filtered by category.
        """
        names = ['cat1', 'cat2', 'cat3', 'cat4']
        for name in names:
            db_catalog_api.category_add(name)
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        _, package1_data = self._test_package()
        _, package2_data = self._test_package()
        _, package3_data = self._test_package()

        package1_data['fully_qualified_name'] += '_1'
        package1_data['name'] += '_1'
        package1_data['class_definitions'] = (u'test.mpl.v1.app.Thing1',)
        package1_data['categories'] = ('cat1', 'cat2')

        package2_data['fully_qualified_name'] += '_2'
        package2_data['name'] += '_2'
        package2_data['class_definitions'] = (u'test.mpl.v1.app.Thing2',)
        package2_data['categories'] = ('cat2', 'cat3')

        package3_data['fully_qualified_name'] += '_3'
        package3_data['name'] += '_3'
        package3_data['class_definitions'] = (u'test.mpl.v1.app.Thing3',)
        package3_data['categories'] = ('cat2', 'cat4')

        expected_packages = [db_catalog_api.package_upload(package1_data, ''),
                             db_catalog_api.package_upload(package2_data, '')]
        db_catalog_api.package_upload(package3_data, '')

        categories_in = "in:cat1,cat3"

        req = self._get('/catalog/packages',
                        params={'category': categories_in})
        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        res = req.get_response(self.api)
        self.assertEqual(200, res.status_code)
        self.assertEqual(2, len(res.json['packages']))

        found_packages = res.json['packages']

        self.assertEqual([pack.id for pack in expected_packages],
                         [pack['id'] for pack in found_packages])

    def test_packages_filter_by_in_tag(self):
        """Test that packages are filtered by in:tag1,tag2,tag3

        GET /catalog/packages with parameter "tag=in:tag1,tag2,tag3"
        returns packages filtered by category.
        """
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        _, package1_data = self._test_package()
        _, package2_data = self._test_package()
        _, package3_data = self._test_package()

        package1_data['fully_qualified_name'] += '_1'
        package1_data['name'] += '_1'
        package1_data['class_definitions'] = (u'test.mpl.v1.app.Thing1',)
        package1_data['tags'] = ('tag1', 'tag2')

        package2_data['fully_qualified_name'] += '_2'
        package2_data['name'] += '_2'
        package2_data['class_definitions'] = (u'test.mpl.v1.app.Thing2',)
        package2_data['tags'] = ('tag2', 'tag3')

        package3_data['fully_qualified_name'] += '_3'
        package3_data['name'] += '_3'
        package3_data['class_definitions'] = (u'test.mpl.v1.app.Thing3',)
        package3_data['tags'] = ('tag2', 'tag4')

        expected_packages = [db_catalog_api.package_upload(package1_data, ''),
                             db_catalog_api.package_upload(package2_data, '')]
        db_catalog_api.package_upload(package3_data, '')

        tag_in = "in:tag1,tag3"

        req = self._get('/catalog/packages',
                        params={'tag': tag_in})
        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        res = req.get_response(self.api)
        self.assertEqual(200, res.status_code)
        self.assertEqual(2, len(res.json['packages']))

        found_packages = res.json['packages']

        self.assertEqual([pack.id for pack in expected_packages],
                         [pack['id'] for pack in found_packages])

    def test_packages_filter_by_in_id(self):
        """Test that packages are filtered by in:id1,id2,id3

        GET /catalog/packages with parameter "id=in:id1,id2" returns packages
        filtered by id.
        """
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        _, package1_data = self._test_package()
        _, package2_data = self._test_package()
        _, package3_data = self._test_package()

        package1_data['fully_qualified_name'] += '_1'
        package1_data['name'] += '_1'
        package1_data['class_definitions'] = (u'test.mpl.v1.app.Thing1',)
        package2_data['fully_qualified_name'] += '_2'
        package2_data['name'] += '_2'
        package2_data['class_definitions'] = (u'test.mpl.v1.app.Thing2',)
        package3_data['fully_qualified_name'] += '_3'
        package3_data['name'] += '_3'
        package3_data['class_definitions'] = (u'test.mpl.v1.app.Thing3',)

        expected_packages = [db_catalog_api.package_upload(package1_data, ''),
                             db_catalog_api.package_upload(package2_data, '')]
        db_catalog_api.package_upload(package3_data, '')

        id_in = "in:" + ",".join(pack.id for pack in expected_packages)

        req = self._get('/catalog/packages',
                        params={'id': id_in})
        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        res = req.get_response(self.api)
        self.assertEqual(200, res.status_code)

        self.assertEqual(2, len(res.json['packages']))

        found_packages = res.json['packages']

        self.assertEqual([pack.id for pack in expected_packages],
                         [pack['id'] for pack in found_packages])

    def test_packages_filter_by_in_id_empty(self):
        """Test that packages are filtered by "id=in:"

        GET /catalog/packages with parameter "id=in:" returns packages
        filtered by id, in this case no packages should be returned.
        """
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        _, package1_data = self._test_package()

        db_catalog_api.package_upload(package1_data, '')

        req = self._get('/catalog/packages', params={'id': "in:"})
        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        res = req.get_response(self.api)
        self.assertEqual(200, res.status_code)

        self.assertEqual(0, len(res.json['packages']))

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

    @mock.patch('murano.api.v1.catalog.LOG')
    def test_packages_filter_by_order_by(self, mock_log):
        warnings = []
        mock_log.warning = lambda msg: warnings.append(msg)

        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        self._add_pkg("test_tenant", type='Library')

        # Test whether a valid order by value works.
        order_by = 'name'
        request = self._get('/catalog/packages',
                            params={'order_by': order_by})

        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        self.controller.search(request)
        self.assertEqual(len(warnings), 0)

        # Test whether an invalid order by value fails.
        order_by = 'TEST ORDER BY'
        request = self._get('/catalog/packages', params={'order_by': order_by})

        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        self.controller.search(request)
        self.assertEqual(len(warnings), 1)
        self.assertIn('parameter is not valid', warnings[0])

    def test_packages_filter_by_limit(self):
        """Test that packages are filtered by limit."""
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        pkg = self._add_pkg("test_tenant", type='Library')

        request = self._get('/catalog/packages', params={'limit': '1'})
        self.expect_policy_check('get_package')

        self.expect_policy_check('manage_public_package')
        res = self.controller.search(request)

        self.assertIn('next_marker', res)
        self.assertEqual(res['next_marker'], pkg['id'])

    def test_packages_filter_by_limit_negative_cases(self):
        """Test whether invalid limit values throw expected exceptions."""
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        self._add_pkg("test_tenant", type='Library')

        # Test wheter non-number value throws exception
        request = self._get('/catalog/packages',
                            params={'limit': 'not a number'})
        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')
        e = self.assertRaises(exc.HTTPBadRequest, self.controller.search,
                              request)
        self.assertEqual(e.explanation, 'Limit param must be an integer')

        # Test whether below-zero value throws exception
        request = self._get('/catalog/packages', params={'limit': '-1'})
        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')
        e = self.assertRaises(exc.HTTPBadRequest, self.controller.search,
                              request)
        self.assertEqual(e.explanation, 'Limit param must be positive')

    @mock.patch('murano.common.utils.split_for_quotes')
    @mock.patch('murano.api.v1.catalog.LOG')
    def test_packages_filter_handle_value_error(self, mock_log, mock_func):
        warnings = []
        mock_func.side_effect = ValueError
        mock_log.warning = lambda msg: warnings.append(msg)

        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        self._add_pkg("test_tenant", type='Library')
        tag_in = "in:tag1,tag3"
        self._get('/catalog/packages', params={'tag': tag_in})
        request = self._get('/catalog/packages',
                            params={'tag': tag_in})

        self.expect_policy_check('get_package')
        self.expect_policy_check('manage_public_package')

        self.controller.search(request)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Search by parameter 'tag' caused an  error",
                      warnings[0])

    def test_packages_filter_by_search(self):
        self._set_policy_rules(
            {'get_package': '',
             'manage_public_package': ''}
        )
        excepted_pkg1 = self._add_pkg("test_tenant",
                                      type='Application',
                                      name='awcloud',
                                      description='some context')
        excepted_pkg2 = self._add_pkg("test_tenant",
                                      type='Application',
                                      name='mysql',
                                      description='awcloud product')
        excepted_pkg3 = self._add_pkg("test_tenant",
                                      type='Application',
                                      name='package3',
                                      author='mysql author')

        # filter by search=awcloud can see 2 pkgs
        req_awc = self._get('/catalog/packages',
                            params={'search': 'awcloud'})

        # filter by search=mysql only see 2 pkgs
        req_mysql = self._get('/catalog/packages',
                              params={'search': 'mysql'})

        for dummy in range(2):
            self.expect_policy_check('get_package')
            self.expect_policy_check('manage_public_package')

        res_awc = req_awc.get_response(self.api)

        self.assertEqual(200, res_awc.status_code)
        self.assertEqual(2, len(res_awc.json['packages']))

        self.assertEqual(excepted_pkg1.name,
                         res_awc.json['packages'][0]['name'])

        self.assertEqual(excepted_pkg2.name,
                         res_awc.json['packages'][1]['name'])

        res_mysql = req_mysql.get_response(self.api)

        self.assertEqual(200, res_mysql.status_code)
        self.assertEqual(2, len(res_mysql.json['packages']))

        self.assertEqual(excepted_pkg2.name,
                         res_mysql.json['packages'][0]['name'])
        self.assertEqual(excepted_pkg3.name,
                         res_mysql.json['packages'][1]['name'])

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

    def test_modify_package_tags(self):
        self._set_policy_rules(
            {'modify_package': '',
             'manage_public_package': '',
             'publicize_package': ''}
        )
        saved_package = self._add_pkg('test_tenant')
        saved_package_pub = self._add_pkg('test_tenant', public=True)
        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package.id})

        url = '/v1/catalog/packages/' + str(saved_package.id)

        data = []
        data.append({'op': 'add', 'path': ['tags'], 'value': ["foo", "bar"]})

        req = self._patch(url, jsonutils.dump_as_bytes(data))
        result = self.controller.update(req, data, saved_package.id)

        self.assertIn('foo', result['tags'])
        self.assertIn('bar', result['tags'])

        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package_pub.id})
        self.expect_policy_check('manage_public_package', {})
        url = '/v1/catalog/packages/' + str(saved_package_pub.id)

        data = []
        data.append({'op': 'add', 'path': ['tags'], 'value': ["foo", "bar"]})

        req = self._patch(url, jsonutils.dump_as_bytes(data))
        result = self.controller.update(req, data, saved_package_pub.id)

        self.assertIn('foo', result['tags'])
        self.assertIn('bar', result['tags'])

    def test_modify_package_name(self):
        self._set_policy_rules(
            {'modify_package': ''}
        )
        saved_package = self._add_pkg('test_tenant')
        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package.id})
        url = '/v1/catalog/packages/' + str(saved_package.id)

        data = []
        data.append({'op': 'replace', 'path': ['name'], 'value': 'test_name'})
        req = self._patch(url, jsonutils.dump_as_bytes(data))
        result = self.controller.update(req, data, saved_package.id)
        self.assertEqual('test_name', result['name'])
        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package.id})

        data = []
        data.append({'op': 'replace', 'path': ['name'], 'value': 'a'*81})
        req = self._patch(url, jsonutils.dump_as_bytes(data))
        self.assertRaises(exc.HTTPBadRequest, self.controller.update,
                          req, data, saved_package.id)

    def test_modify_package_no_body(self):
        self._set_policy_rules(
            {'modify_package': ''}
        )
        saved_package = self._add_pkg('test_tenant')
        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package.id})
        url = '/v1/catalog/packages/' + str(saved_package.id)
        req = self._patch(url, jsonutils.dump_as_bytes(None))
        self.assertRaises(exc.HTTPBadRequest, self.controller.update,
                          req, None, saved_package.id)

    def test_modify_package_is_public(self):
        self._set_policy_rules(
            {'modify_package': '',
             'manage_public_package': '',
             'publicize_package': ''}
        )
        saved_package = self._add_pkg('test_tenant')
        url = '/v1/catalog/packages/' + str(saved_package.id)
        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package.id})
        self.expect_policy_check('publicize_package', {})
        data = []
        data.append({'op': 'replace', 'path': ['is_public'], 'value': True})
        req = self._patch(url, jsonutils.dump_as_bytes(data))
        result = self.controller.update(req, data, saved_package.id)
        self.assertTrue(result['is_public'])

    def test_modify_package_bad_content_type(self):
        self._set_policy_rules(
            {'modify_package': '',
             'manage_public_package': '',
             'publicize_package': ''}
        )
        saved_package = self._add_pkg('test_tenant')
        url = '/v1/catalog/packages/' + str(saved_package.id)
        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package.id})
        self.expect_policy_check('publicize_package', {})
        data = []
        data.append({'op': 'replace', 'path': ['is_public'], 'value': True})
        req = self._patch(url, jsonutils.dump_as_bytes(data))
        result = self.controller.update(req, data, saved_package.id)
        self.assertTrue(result['is_public'])

    def test_modify_package_with_incorrect_content_type(self):
        self._set_policy_rules(
            {'modify_package': ''}
        )
        saved_package = self._add_pkg('test_tenant')
        self.expect_policy_check('modify_package',
                                 {'package_id': saved_package.id})
        url = '/v1/catalog/packages/' + str(saved_package.id)
        data = []
        data.append({'op': 'replace', 'path': ['name'], 'value': 'test_name'})

        req = self._patch(url, jsonutils.dump_as_bytes(data))
        req.get_content_type = mock.MagicMock(
            side_effect=common_exc.UnsupportedContentType)
        self.assertRaises(exc.HTTPBadRequest,
                          self.controller.update, req, data, saved_package.id)

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
        self.assertIn(b'Acceptable response can not be provided',
                      result.body)

    @mock.patch('murano.api.v1.catalog._validate_body')
    @mock.patch('murano.common.policy.check')
    def test_upload_package_with_invalid_schema(self, mock_policy_check,
                                                mock_validate_body):
        invalid_pkg_upload_schema = {"type": None}
        mock_policy_check.return_value = True
        mock_validate_body.return_value = (None, invalid_pkg_upload_schema)
        mock_request = mock.MagicMock(context={})
        e = self.assertRaises(exc.HTTPBadRequest, self.controller.upload,
                              mock_request)
        self.assertIn(
            "Package schema is not valid",
            e.explanation
        )

    @mock.patch('murano.api.v1.catalog._validate_body')
    @mock.patch('murano.common.policy.check')
    def test_upload_package_with_invalid_file_content(self, mock_policy_check,
                                                      mock_validate_body):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            mock_policy_check.return_value = True
            mock_validate_body.return_value = (mock.MagicMock(file=temp_file),
                                               None)
            mock_request = mock.MagicMock(context={})
            e = self.assertRaises(exc.HTTPBadRequest, self.controller.upload,
                                  mock_request)
            self.assertIn(
                "Uploading file can't be empty",
                e.explanation
            )

    @mock.patch('murano.api.v1.catalog.PKG_PARAMS_MAP')
    @mock.patch('murano.packages.load_utils.load_from_file')
    @mock.patch('murano.api.v1.catalog._validate_body')
    @mock.patch('murano.common.policy.check')
    def test_upload_package_with_oversized_file_name(self, mock_policy_check,
                                                     mock_validate_body,
                                                     mock_load_from_file,
                                                     mock_pkg_params_map):
        mock_policy_check.return_value = True
        mock_load_from_file.return_value = mock.MagicMock(
            __exit__=lambda obj, type, value, tb: False)
        mock_pkg_params_map.return_value = {}
        mock_request = mock.MagicMock(context=mock.MagicMock(
            tenant=self.tenant))
        test_package_meta = {'name': 'a'*81}
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"Random test content\n")
            temp_file.seek(0)
            mock_validate_body.return_value = \
                (mock.MagicMock(file=temp_file), test_package_meta)
            e = self.assertRaises(exc.HTTPBadRequest, self.controller.upload,
                                  mock_request)
            self.assertIn(
                "Package name should be 80 characters maximum",
                e.explanation
            )

    @mock.patch('murano.packages.load_utils.load_from_file')
    @mock.patch('murano.api.v1.catalog._validate_body')
    @mock.patch('murano.common.policy.check')
    def test_upload_package_handle_package_load_error(self, mock_policy_check,
                                                      mock_validate_body,
                                                      mock_load_from_file):
        pkg_to_upload = mock.MagicMock(
            __exit__=lambda obj, type, value, tb: False)
        mock_request = mock.MagicMock(context=mock.MagicMock(
            tenant=self.tenant))
        mock_load_from_file.return_value = pkg_to_upload
        mock_load_from_file.side_effect = exceptions.PackageLoadError
        mock_policy_check.return_value = True
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"Random test content\n")
            temp_file.seek(0)
            mock_validate_body.return_value = \
                (mock.MagicMock(file=temp_file), None)
            e = self.assertRaises(exc.HTTPBadRequest, self.controller.upload,
                                  mock_request)
            self.assertIn(
                "Couldn't load package from file",
                e.explanation
            )

    @mock.patch('murano.packages.load_utils.load_from_file')
    @mock.patch('murano.api.v1.catalog._validate_body')
    @mock.patch('murano.common.policy.check')
    def test_upload_package_handle_duplicate_exception(self, mock_policy_check,
                                                       mock_validate_body,
                                                       mock_load_from_file):
        """Test whether duplicate error is correctly thrown."""
        # Save the first package entry to the DB
        test_package_meta = self.test_package.copy()
        test_package_meta['name'] = 'test_package'
        test_package_meta['fully_qualified_name'] = str(uuid.uuid4())
        test_package_meta['description'] = 'test_description'
        test_package_meta['enabled'] = False
        test_package_meta['is_public'] = False
        db_catalog_api.package_upload(test_package_meta, self.tenant)

        # Reverse the operation performed by upload for copying values from
        # pkg_to_upload into package_meta dict.
        pkg_to_upload = mock.MagicMock(
            __exit__=lambda obj, type, value, tb: False)
        for k, v in PKG_PARAMS_MAP.items():
            if v in test_package_meta.keys():
                val = test_package_meta[v]
                setattr(pkg_to_upload.__enter__(), k, val)

        # Delete extra properties so validation in upload passes.
        for attr in ['fully_qualified_name', 'ui_definition', 'author',
                     'supplier_logo', 'supplier', 'logo', 'type', 'archive']:
            if attr in test_package_meta.keys():
                del test_package_meta[attr]

        mock_request = mock.MagicMock(context=mock.MagicMock(
            tenant=self.tenant))
        mock_load_from_file.return_value = pkg_to_upload
        mock_policy_check.return_value = True

        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(b"Random test content\n")
            temp_file.seek(0)
            mock_validate_body.return_value = \
                (mock.MagicMock(file=temp_file), test_package_meta)
            e = self.assertRaises(exc.HTTPConflict, self.controller.upload,
                                  mock_request)
            self.assertIn(
                "Package with specified full name is already registered",
                e.detail
            )

    @mock.patch('murano.common.policy.check')
    def test_upload_package_with_oversized_body(self, mock_policy_check):
        mock_policy_check.return_value = True
        packages_to_upload = {'a': 0, 'b': 1, 'c': 2}
        mock_request = mock.MagicMock(context={})
        e = self.assertRaises(exc.HTTPBadRequest, self.controller.upload,
                              mock_request, body=packages_to_upload)
        self.assertIn(
            "'multipart/form-data' request body should contain 1 or 2 "
            "parts: json string and zip archive.",
            e.explanation
        )

    @mock.patch('murano.common.policy.check')
    def test_upload_package_with_empty_body(self, mock_policy_check):
        mock_policy_check.return_value = True
        packages_to_upload = {}
        mock_request = mock.MagicMock(context={})
        e = self.assertRaises(exc.HTTPBadRequest, self.controller.upload,
                              mock_request, body=packages_to_upload)
        self.assertEqual(
            'There is no file package with application description',
            e.explanation)

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
        self.assertIn(b'Acceptable response can not be provided',
                      result.body)

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
        self.assertIn(b'Acceptable response can not be provided',
                      result.body)

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

    def test_upload_pkg_with_tag(self):
        """Check upload package with tags successfully"""

        self._set_policy_rules({'upload_package': '@'})
        self.expect_policy_check('upload_package')
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

            # Uploading a package with foo_tag
            req = self._post(
                '/catalog/packages',
                format_body({'tags': ['foo_tag']}),
                content_type='multipart/form-data; ; boundary=BOUNDARY',
            )
            res = req.get_response(self.api)

            processed_result = jsonutils.loads(res.body)
            # check user set foo_tag in result
            self.assertIn('foo_tag', processed_result["tags"])
            # check tag Linux from package in result
            self.assertIn('Linux', processed_result["tags"])

    def test_add_category(self):
        """Check that category added successfully"""

        self._set_policy_rules({'add_category': '@'})
        self.expect_policy_check('add_category')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        expected = {
            'name': 'new_category',
            'created': datetime.isoformat(fake_now)[:-7],
            'updated': datetime.isoformat(fake_now)[:-7],
            'package_count': 0,
        }

        body = {'name': 'new_category'}
        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        processed_result = jsonutils.loads(result.body)
        self.assertIn('id', processed_result.keys())
        expected['id'] = processed_result['id']
        self.assertEqual(expected, processed_result)

    def test_get_category(self):
        """Check that get category executed successfully"""

        self._set_policy_rules({'add_category': '@', 'get_category': '@'})
        self.expect_policy_check('add_category')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        expected = {
            'name': 'new_category',
            'created': datetime.isoformat(fake_now)[:-7],
            'updated': datetime.isoformat(fake_now)[:-7],
            'package_count': 0,
            'packages': []
        }

        body = {'name': 'new_category'}
        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        expected['id'] = jsonutils.loads(result.body)['id']

        self.expect_policy_check('get_category')
        req = self._get('/catalog/categories/%s' % expected['id'])
        retrieved_category = jsonutils.loads(req.get_response(self.api).body)
        self.assertEqual(retrieved_category, expected)

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

    @mock.patch('murano.db.catalog.api.category_get')
    def test_delete_category_with_packages_negative(self, mock_get_category):
        """Check that deleting category that has assigned packages fails."""
        mock_get_category.return_value = mock.MagicMock(
            packages=['test_package'])

        self._set_policy_rules({'delete_category': '@'})
        self.expect_policy_check('delete_category',
                                 {'category_id': '12345'})

        fake_now = timeutils.utcnow()
        expected = {'name': 'new_category',
                    'created': fake_now,
                    'updated': fake_now,
                    'id': '12345'}

        category = models.Category(**expected)
        test_utils.save_models(category)

        req = self._delete('/catalog/categories/12345')
        e = self.assertRaises(exc.HTTPForbidden,
                              self.controller.delete_category, req, '12345')
        self.assertEqual(e.explanation,
                         "It's impossible to delete categories assigned to the"
                         " package, uploaded to the catalog")

    def test_add_category_without_name(self):
        """Test whether adding a category without a name throws exception."""
        self._set_policy_rules({'add_category': '@'})
        self.expect_policy_check('add_category')

        body = {'name': ''}
        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        e = self.assertRaises(exc.HTTPBadRequest, self.controller.add_category,
                              req, body)
        self.assertEqual("Please, specify a name of the category to create",
                         e.explanation)

    def test_add_category_handle_duplicate_exception(self):
        """Test whether creating duplicate categories throws exception."""
        self._set_policy_rules({'add_category': '@'})
        self.expect_policy_check('add_category')
        self.expect_policy_check('add_category')

        body = {'name': 'new_category'}
        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        self.controller.add_category(req, body)

        req = self._post('/catalog/categories', jsonutils.dump_as_bytes(body))
        e = self.assertRaises(exc.HTTPConflict, self.controller.add_category,
                              req, body)
        self.assertEqual("Category with specified name is already exist",
                         e.explanation)

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

        Check that a category that contains more than 80 characters
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

    def test_list_categories(self):
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

    def test_list_categories_negative(self):
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
