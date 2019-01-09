# Copyright 2016 OpenStack Foundation.
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

"""Increase time resolution for status reports

Revision ID: 014
Create Date: 2016-04-28

"""

from alembic import op
import sqlalchemy.dialects.mysql as sa_mysql

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def _check_dbms(engine):
    dialect = engine.dialect.dialect_description
    version = engine.dialect.server_version_info
    if dialect.startswith('mysql') and version >= (5, 6, 4):
        return True
    if 'MariaDB' in version and version >= (5, 3):
        return True
    return False


def upgrade():
    engine = op.get_bind()
    if _check_dbms(engine):
        with op.batch_alter_table('status') as batch_op:
            batch_op.alter_column(
                'created', type_=sa_mysql.DATETIME(fsp=6), nullable=False)
            batch_op.alter_column(
                'updated', type_=sa_mysql.DATETIME(fsp=6), nullable=False)


def downgrade():
    engine = op.get_bind()
    if _check_dbms(engine):
        with op.batch_alter_table('status') as batch_op:
            batch_op.alter_column(
                'created', type_=sa_mysql.DATETIME(), nullable=False)
            batch_op.alter_column(
                'updated', type_=sa_mysql.DATETIME(), nullable=False)
