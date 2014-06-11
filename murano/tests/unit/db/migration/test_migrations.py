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

import datetime
import uuid

from oslo.config import cfg
from oslo.db.sqlalchemy import utils as db_utils
from sqlalchemy import exc

from murano.db.migration import migration
from murano.db import models  # noqa
from murano.tests.unit.db.migration import test_migrations_base as base

CONF = cfg.CONF


class TestMigrations(base.BaseWalkMigrationTestCase, base.CommonTestsMixIn):

    USER = "openstack_citest"
    PASSWD = "openstack_citest"
    DATABASE = "openstack_citest"

    def __init__(self, *args, **kwargs):
        super(TestMigrations, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestMigrations, self).setUp()

    def assertColumnExists(self, engine, table, column):
        t = db_utils.get_table(engine, table)
        self.assertIn(column, t.c)

    def assertColumnsExists(self, engine, table, columns):
        for column in columns:
            self.assertColumnExists(engine, table, column)

    def assertColumnCount(self, engine, table, columns):
        t = db_utils.get_table(engine, table)
        self.assertEqual(len(t.columns), len(columns))

    def assertColumnNotExists(self, engine, table, column):
        t = db_utils.get_table(engine, table)
        self.assertNotIn(column, t.c)

    def assertIndexExists(self, engine, table, index):
        t = db_utils.get_table(engine, table)
        index_names = [idx.name for idx in t.indexes]
        self.assertIn(index, index_names)

    def assertIndexMembers(self, engine, table, index, members):
        self.assertIndexExists(engine, table, index)

        t = db_utils.get_table(engine, table)
        index_columns = None
        for idx in t.indexes:
            if idx.name == index:
                index_columns = idx.columns.keys()
                break

        self.assertEqual(sorted(members), sorted(index_columns))

    def _check_001(self, engine, data):
        self.assertEqual('001', migration.version(engine))
        self.assertColumnExists(engine, 'category', 'id')
        self.assertColumnExists(engine, 'environment', 'tenant_id')

        # make sure indexes are in place
        self.assertIndexExists(engine,
                               'class_definition',
                               'ix_class_definition_name')

        self.assertIndexExists(engine,
                               'package',
                               'ix_package_fqn')
        self.assertIndexExists(engine,
                               'category',
                               'ix_category_name')

        self._test_package_fqn_is_uniq(engine)

    def _test_package_fqn_is_uniq(self, engine):
        package_table = db_utils.get_table(engine, 'package')

        package = {
            'id': str(uuid.uuid4()),
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
            'owner_id': '123',
            'created': datetime.datetime.now(),
            'updated': datetime.datetime.now()
        }
        package_table.insert().execute(package)

        package['id'] = str(uuid.uuid4())
        self.assertRaises(exc.IntegrityError,
                          package_table.insert().execute, package)

    def _check_002(self, engine, data):
        self.assertEqual('002', migration.version(engine))
        self.assertColumnExists(engine, 'package', 'supplier_logo')

    def _check_003(self, engine, data):
        self.assertEqual('003', migration.version(engine))
        self.assertColumnExists(engine, 'task', 'action')
        self.assertColumnExists(engine, 'status', 'task_id')
