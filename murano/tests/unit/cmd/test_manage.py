# Copyright (c) 2016 AT&T Corp
# All Rights Reserved.
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

import mock
from oslo_config import cfg

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from murano.cmd import manage
from murano.db.catalog import api as db_catalog_api
from murano.db import models
from murano.db import session as db_session
from murano.tests.unit import base as test_base

CONF = cfg.CONF


class TestManage(test_base.MuranoWithDBTestCase):

    def setUp(self):
        super(TestManage, self).setUp()

        session = db_session.get_session()
        # Create environment.
        self.test_environment = models.Environment(
            name=b'test_environment', tenant_id=b'test_tenant_id',
            version=1
        )
        # Create categories.
        self.test_categories = [
            models.Category(name=b'test_category_1'),
            models.Category(name=b'test_category_2')
        ]
        # Create tags.
        self.test_tags = [
            models.Tag(name=b'test_tag_1'),
            models.Tag(name=b'test_tag_2')
        ]
        # Add environment, categories and tags to DB.
        with session.begin():
            session.add(self.test_environment)
            session.add_all(self.test_categories)
            session.add_all(self.test_tags)
        # Create package.
        self.test_package = models.Package(
            fully_qualified_name=b'test_fqn', name=b'test_name',
            logo=b'test_logo', supplier_logo=b'test_supplier_logo',
            type=b'test_type', description=b'test_desc', is_public=True,
            archive=b'test_archive', ui_definition=b'test_ui_definition',
            categories=self.test_categories, tags=self.test_tags,
            owner_id=self.test_environment.tenant_id,)
        # Add the package to the DB.
        with session.begin():
            session.add(self.test_package)
        # Create class definitions and assign their FKs to test_package.id.
        self.test_class_definitions = [
            models.Class(name=b'test_class_definition_1',
                         package_id=self.test_package.id),
            models.Class(name=b'test_class_definition_2',
                         package_id=self.test_package.id)
        ]
        # Add the class definitions to the DB and update the FK reference for
        # test_package.class_definitions.
        with session.begin():
            session.add_all(self.test_class_definitions)
            self.test_package.class_definitions = self.test_class_definitions
            session.add(self.test_package)
        # Create mock object that resembles loaded package from
        # load_utils.load_from_dir
        self.mock_loaded_package = mock.MagicMock(
            full_name=self.test_package.fully_qualified_name,
            display_name=self.test_package.name,
            package_type=self.test_package.type,
            author=self.test_package.author,
            supplier=self.test_package.supplier,
            description=self.test_package.description,
            tags=[tag.name for tag in self.test_package.tags],
            classes=[cls.name for cls in self.test_package.class_definitions],
            logo=self.test_package.logo,
            supplier_logo=self.test_package.supplier_logo,
            ui=self.test_package.ui_definition,
            blob=self.test_package.archive)

    @mock.patch('murano.cmd.manage.LOG')
    @mock.patch('murano.cmd.manage.load_utils')
    def test_do_import_package(self, mock_load_utils, mock_log):
        manage.CONF = mock.MagicMock()
        manage.CONF.command = mock.MagicMock(
            directory='test_dir',
            categories=[cat.name for cat in self.test_package.categories],
            update=True)
        mock_load_utils.load_from_dir.return_value = self.mock_loaded_package

        manage.do_import_package()

        # Assert that the function ran to completion.
        self.assertIn("Finished import of package",
                      str(mock_log.info.mock_calls[0]))

        # Check that the package was uploaded to the DB.
        filter_params = {
            'name': self.test_package.name,
            'fully_qualified_name': self.test_package.fully_qualified_name,
            'type': self.test_package.type,
            'description': self.test_package.description
        }
        retrieved_package = None
        session = db_session.get_session()
        with session.begin():
            retrieved_package = session.query(models.Package)\
                .filter_by(**filter_params).first()
        self.assertIsNotNone(retrieved_package)
        self.assertNotEqual(self.test_package.id, retrieved_package.id)

    @mock.patch('murano.cmd.manage.LOG')
    @mock.patch('murano.cmd.manage.load_utils')
    @mock.patch('murano.cmd.manage.db_catalog_api')
    def test_do_import_package_without_update(self, mock_db_catalog_api,
                                              mock_load_utils, mock_log):
        mock_db_catalog_api.package_search.return_value =\
            [self.test_package]
        mock_load_utils.load_from_dir.return_value =\
            mock.MagicMock(full_name='test_full_name')
        manage.CONF = mock.MagicMock()
        manage.CONF.command = mock.MagicMock(
            directory='test_dir',
            categories=[],
            update=False)

        manage.do_import_package()

        mock_log.error.assert_called_once_with(
            "Package '{name}' exists ({pkg_id}). Use --update."
                .format(name='test_full_name', pkg_id=self.test_package.id))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_do_list_categories(self, mock_stdout):
        expected_output = ">> Murano package categories:* "\
                          "test_category_1* test_category_2"

        manage.do_list_categories()
        self.assertEqual(expected_output,
                         mock_stdout.getvalue().replace('\n', '')
                         .replace('b\'', '').replace('\'', ''))

    @mock.patch('murano.cmd.manage.db_catalog_api')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_do_list_categories_with_no_categories(self, mock_stdout,
                                                   mock_db_catalog_api):
        mock_db_catalog_api.category_get_names.return_value = []
        expected_output = "No categories were found"

        manage.do_list_categories()

        self.assertEqual(
            expected_output, mock_stdout.getvalue().replace('\n', ''))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_do_add_category(self, mock_stdout):
        manage.CONF = mock.MagicMock()
        manage.CONF.command.category_name = 'test_category_name'

        expected_output = ">> Successfully added category test_category_name"

        manage.do_add_category()

        self.assertEqual(expected_output,
                         mock_stdout.getvalue().replace('\n', ''))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_do_add_category_except_duplicate_error(self, mock_stdout):
        manage.CONF = mock.MagicMock()
        manage.CONF.command.category_name = 'test_category_name'

        expected_output = ">> ERROR: Category \'test_category_name\' already "\
                          "exists"

        db_catalog_api.category_add('test_category_name')
        manage.do_add_category()

        self.assertEqual(expected_output,
                         mock_stdout.getvalue().replace('\n', ''))

    def test_add_command_parsers(self):
        mock_parser = mock.MagicMock()
        mock_subparsers = mock.MagicMock()
        mock_subparsers.add_parser.return_value = mock_parser

        manage.add_command_parsers(mock_subparsers)

        mock_subparsers.add_parser.assert_any_call('import-package')
        mock_subparsers.add_parser.assert_any_call('category-list')
        mock_subparsers.add_parser.assert_any_call('category-add')

        mock_parser.set_defaults.assert_any_call(func=manage.do_import_package)
        mock_parser.set_defaults.assert_any_call(
            func=manage.do_list_categories)
        mock_parser.set_defaults.assert_any_call(func=manage.do_add_category)
        self.assertEqual(4, mock_parser.add_argument.call_count)

    @mock.patch('murano.cmd.manage.CONF')
    def test_main_except_runtime_error(self, mock_conf):
        mock_conf.side_effect = RuntimeError

        with self.assertRaisesRegex(SystemExit, 'ERROR:'):
            manage.main()

    @mock.patch('murano.cmd.manage.CONF')
    def test_main_except_general_exception(self, mock_conf):
        mock_conf.command.func.side_effect = Exception

        expected_err_msg = "murano-manage command failed:"

        with self.assertRaisesRegex(SystemExit, expected_err_msg):
            manage.main()
