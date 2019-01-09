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

"""Increase the size of the text columns storing object model in the task table

Revision ID: 016
Revises: 015
Create Date: 2016-08-30 10:45:00

"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.mysql as sa_mysql

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    engine = op.get_bind()
    if engine.dialect.dialect_description.startswith('mysql'):
        with op.batch_alter_table('task') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa_mysql.LONGTEXT())


def downgrade():
    engine = op.get_bind()
    if engine.dialect.dialect_description.startswith('mysql'):
        with op.batch_alter_table('task') as batch_op:
            batch_op.alter_column('description',
                                  type_=sa.TEXT())
