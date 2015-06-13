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

import murano.db.migration.helpers as helpers
from murano.db.sqla import types as st

"""fix_unique_constraints

Revision ID: 008
Revises: 007
Create Date: 2015-04-08 14:01:06.458512

"""

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'

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
                  nullable=False),
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

    helpers.transform_table(
        'class_definition', {}, {},
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name',
                  sa.String(length=128),
                  nullable=False),
        sa.Column('package_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

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

    op.create_index('ix_package_fqn_and_owner', table_name='package',
                    columns=['fully_qualified_name', 'owner_id'], unique=True)
    op.create_index('ix_class_definition_name',
                    'class_definition',
                    ['name'])


def downgrade():
    op.drop_index('ix_package_fqn_and_owner', table_name='package')
    op.drop_index('ix_class_definition_name', table_name='class_definition')

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
        'class_definition', {}, {},
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name',
                  sa.String(length=128),
                  nullable=False,
                  unique=True),
        sa.Column('package_id', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

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

    op.create_index('ix_class_definition_name',
                    'class_definition',
                    ['name'])
