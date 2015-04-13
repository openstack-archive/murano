# Copyright 2015 OpenStack Foundation.
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


from alembic import op
import sqlalchemy as sa

"""add_locks

Revision ID: 007
Revises: 006
Create Date: 2015-04-08 14:01:06.458512

"""

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.create_table(
        'locks',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET)


def downgrade():
    op.drop_table('locks')
