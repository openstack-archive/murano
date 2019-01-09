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
Change type of description field in package table.

Revision ID: 004
Revises: table package

"""
from alembic import op
import sqlalchemy as sa

import murano.db.migration.helpers as helpers
from murano.db.sqla import types as st

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    engine = op.get_bind()
    if engine.dialect.dialect_description.startswith('mysql'):
        engine.execute('SET FOREIGN_KEY_CHECKS=0')

    if engine.dialect.dialect_description == 'postgresql+psycopg2':
        op.drop_constraint('package_to_tag_package_id_fkey',
                           'package_to_tag', 'foreignkey')
        op.drop_constraint('package_to_tag_tag_id_fkey',
                           'package_to_tag', 'foreignkey')
        op.drop_constraint('package_to_category_package_id_fkey',
                           'package_to_category', 'foreignkey')
        op.drop_constraint('class_definition_package_id_fkey',
                           'class_definition', 'foreignkey')

    helpers.transform_table(
        'package', {}, {},
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('archive', st.LargeBinary(), nullable=True),
        sa.Column('fully_qualified_name',
                  sa.String(length=128),
                  nullable=False,
                  unique=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('author', sa.String(length=80), nullable=True),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('logo', st.LargeBinary(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('ui_definition', sa.Text(), nullable=True),
        sa.Column('supplier_logo', sa.types.LargeBinary),
        sa.Column('supplier', sa.types.Text()),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_package_fqn',
                    'package',
                    ['fully_qualified_name'])

    if engine.dialect.dialect_description.startswith('mysql'):
        engine.execute('SET FOREIGN_KEY_CHECKS=1')

    if engine.dialect.dialect_description == 'postgresql+psycopg2':
        op.create_foreign_key('package_to_tag_package_id_fkey',
                              'package_to_tag', 'package',
                              ['package_id'], ['id'])

        op.create_foreign_key('package_to_tag_tag_id_fkey',
                              'package_to_tag', 'tag',
                              ['tag_id'], ['id'])

        op.create_foreign_key('package_to_category_package_id_fkey',
                              'package_to_category', 'package',
                              ['package_id'], ['id'])

        op.create_foreign_key('class_definition_package_id_fkey',
                              'class_definition', 'package',
                              ['package_id'], ['id'])

    # end Alembic commands #


def downgrade():
    engine = op.get_bind()
    if engine.dialect.dialect_description.startswith('mysql'):
        engine.execute('SET FOREIGN_KEY_CHECKS=0')

    if engine.dialect.dialect_description == 'postgresql+psycopg2':
        op.drop_constraint('package_to_tag_package_id_fkey',
                           'package_to_tag', 'foreignkey')
        op.drop_constraint('package_to_tag_tag_id_fkey',
                           'package_to_tag', 'foreignkey')
        op.drop_constraint('package_to_category_package_id_fkey',
                           'package_to_category', 'foreignkey')
        op.drop_constraint('class_definition_package_id_fkey',
                           'class_definition', 'foreignkey')

    helpers.transform_table(
        'package', {}, {},
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('archive', st.LargeBinary(), nullable=True),
        sa.Column('fully_qualified_name',
                  sa.String(length=128),
                  nullable=False,
                  unique=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('author', sa.String(length=80), nullable=True),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('description', sa.String(length=512), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('logo', st.LargeBinary(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('ui_definition', sa.Text(), nullable=True),
        sa.Column('supplier_logo', sa.types.LargeBinary),
        sa.Column('supplier', sa.types.Text()),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_package_fqn',
                    'package',
                    ['fully_qualified_name'])

    if engine.dialect.dialect_description.startswith('mysql'):
        engine.execute('SET FOREIGN_KEY_CHECKS=1')

    if engine.dialect.dialect_description == 'postgresql+psycopg2':
        op.create_foreign_key('package_to_tag_package_id_fkey',
                              'package_to_tag', 'package',
                              ['package_id'], ['id'])

        op.create_foreign_key('package_to_tag_tag_id_fkey',
                              'package_to_tag', 'tag',
                              ['tag_id'], ['id'])

        op.create_foreign_key('package_to_category_package_id_fkey',
                              'package_to_category', 'package',
                              ['package_id'], ['id'])

        op.create_foreign_key('class_definition_package_id_fkey',
                              'class_definition', 'package',
                              ['package_id'], ['id'])

    # end Alembic commands #
