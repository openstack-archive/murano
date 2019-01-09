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

"""Increase the size of the text columns storing object model

Revision ID: 013
Revises: 012
Create Date: 2016-04-12 15:46:12.251155

"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.mysql as sa_mysql

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    engine = op.get_bind()
    if engine.dialect.dialect_description.startswith('mysql'):
        with op.batch_alter_table('session') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa_mysql.LONGTEXT())
        with op.batch_alter_table('environment') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa_mysql.LONGTEXT())
        with op.batch_alter_table('environment-template') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa_mysql.LONGTEXT())


def downgrade():
    engine = op.get_bind()
    if engine.dialect.dialect_description.startswith('mysql'):
        with op.batch_alter_table('session') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa.TEXT())
        with op.batch_alter_table('environment') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa.TEXT())
        with op.batch_alter_table('environment-template') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa.TEXT())
