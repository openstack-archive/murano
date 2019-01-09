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
Revision ID: 009
Revises: None
Create Date: 2015-08-17 16:34:33.698760

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.create_table(
        'cf_orgs',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('tenant', sa.String(length=255), nullable=False),
        sa.UniqueConstraint('tenant'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET)

    op.create_table(
        'cf_spaces',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('environment_id', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environment.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET)

    op.create_table(
        'cf_serv_inst',
        sa.Column('id', sa.String(length=255), primary_key=True),
        sa.Column('service_id', sa.String(255), nullable=False),
        sa.Column('environment_id', sa.String(255), nullable=False),
        sa.Column('tenant', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environment.id'],),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET)
    # end Alembic commands #


def downgrade():
    op.drop_table('cf_orgs')
    op.drop_table('cf_spaces')
    op.drop_table('cf_serv_inst')
    # end Alembic commands #
