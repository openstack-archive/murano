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
Add action column to deployment table.

Revision ID: 003
Revises: table deployment
Create Date: 2014-07-30 16:11:33.244

"""
from alembic import op
import sqlalchemy as sa

import murano.db.migration.helpers as helpers

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.rename_table('deployment', 'task')
    op.add_column(
        'task',
        sa.Column('action', sa.types.Text())
    )
    op.create_table(
        'deployment',
        sa.Column('id', sa.String(length=36), nullable=False))

    helpers.transform_table(
        'status', {'deployment_id': 'task_id'}, {},
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('entity', sa.String(length=10), nullable=True),
        sa.Column('task_id', sa.String(length=36), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.drop_table('deployment')


def downgrade():
    op.drop_column('task', 'action')
    op.rename_table('task', 'deployment')

    op.create_table(
        'task',
        sa.Column('id', sa.String(length=36), nullable=False))

    helpers.transform_table(
        'status', {'task_id': 'deployment_id'}, {},
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('entity', sa.String(length=10), nullable=True),
        sa.Column('deployment_id', sa.String(length=36), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['deployment_id'], ['deployment.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.drop_table('task')
    # end Alembic commands #
