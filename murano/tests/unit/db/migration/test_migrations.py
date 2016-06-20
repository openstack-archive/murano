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

"""
Tests for database migrations.
For the opportunistic testing you need to set up a db named 'openstack_citest'
with user 'openstack_citest' and password 'openstack_citest' on localhost.
The test will then use that db and u/p combo to run the tests.
For postgres on Ubuntu this can be done with the following commands:
sudo -u postgres psql
postgres=# create user openstack_citest with createdb login password
      'openstack_citest';
postgres=# create database openstack_citest with owner openstack_citest;
"""

import datetime
import uuid

from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import test_base
from oslo_db.sqlalchemy import utils as db_utils
import sqlalchemy

from murano.db.migration import migration
from murano.tests.unit.db.migration import test_migrations_base as base


class MuranoMigrationsCheckers(object):

    snake_walk = True
    downgrade = True

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

    def assertColumnType(self, engine, table, column, sqltype):
        t = db_utils.get_table(engine, table)
        col = getattr(t.c, column)
        self.assertIsInstance(col.type, sqltype)

    def assertIndexMembers(self, engine, table, index, members):
        self.assertIndexExists(engine, table, index)

        t = db_utils.get_table(engine, table)
        index_columns = None
        for idx in t.indexes:
            if idx.name == index:
                index_columns = idx.columns.keys()
                break

        self.assertEqual(sorted(members), sorted(index_columns))

    def test_walk_versions(self):
        self.walk_versions(self.engine, self.snake_walk, self.downgrade)

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
            'archive': b"archive blob here",
            'fully_qualified_name': 'com.example.package',
            'type': 'class',
            'author': 'OpenStack',
            'name': 'package',
            'enabled': True,
            'description': 'some text',
            'is_public': False,
            'tags': ['tag1', 'tag2'],
            'logo': b"logo blob here",
            'ui_definition': '{}',
            'owner_id': '123',
            'created': datetime.datetime.now(),
            'updated': datetime.datetime.now()
        }
        package_table.insert().execute(package)

        package['id'] = str(uuid.uuid4())
        self.assertRaises(db_exc.DBDuplicateEntry,
                          package_table.insert().execute, package)

    def _check_002(self, engine, data):
        self.assertEqual('002', migration.version(engine))
        self.assertColumnsExists(engine,
                                 'package',
                                 ['supplier_logo', 'supplier'])

    def _check_003(self, engine, data):
        self.assertEqual('003', migration.version(engine))
        self.assertColumnExists(engine, 'task', 'action')
        self.assertColumnExists(engine, 'status', 'task_id')

    def _check_004(self, engine, data):
        self.assertEqual('004', migration.version(engine))
        self.assertColumnType(engine,
                              'package',
                              'description',
                              sqlalchemy.Text)

    def _check_005(self, engine, data):
        self.assertEqual('005', migration.version(engine))
        self.assertColumnExists(engine, 'environment-template', 'id')
        self.assertColumnExists(engine, 'environment-template', 'tenant_id')
        self.assertColumnExists(engine, 'environment-template', 'name')

    def _check_006(self, engine, data):
        self.assertEqual('006', migration.version(engine))
        self.assertColumnExists(engine, 'task', 'result')

    def _check_007(self, engine, data):
        self.assertEqual('007', migration.version(engine))
        self.assertColumnExists(engine, 'locks', 'id')
        self.assertColumnExists(engine, 'locks', 'ts')

    def _check_008(self, engine, data):
        self.assertEqual('008', migration.version(engine))
        self.assertIndexExists(engine,
                               'class_definition',
                               'ix_class_definition_name')

        self.assertIndexExists(engine,
                               'package',
                               'ix_package_fqn_and_owner')


class TestMigrationsMySQL(MuranoMigrationsCheckers,
                          base.BaseWalkMigrationTestCase,
                          test_base.MySQLOpportunisticTestCase):
    pass


class TestMigrationsPostgresql(MuranoMigrationsCheckers,
                               base.BaseWalkMigrationTestCase,
                               test_base.PostgreSQLOpportunisticTestCase):
    pass
