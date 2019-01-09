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

"""empty message

Revision ID: 001
Revises: None
Create Date: 2014-05-29 16:32:33.698760

"""
import uuid

from alembic import op
from oslo_utils import timeutils
import sqlalchemy as sa
from sqlalchemy.sql.expression import table as sa_table

from murano.common import consts
from murano.db.sqla import types as st

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def _create_default_categories(op):
    bind = op.get_bind()
    table = sa_table(
        'category',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('created', sa.DateTime()),
        sa.Column('updated', sa.DateTime()),
        sa.Column('name', sa.String(length=80)))

    now = timeutils.utcnow()

    for category in consts.CATEGORIES:
        values = {'id': uuid.uuid4().hex,
                  'name': category,
                  'updated': now,
                  'created': now}
        bind.execute(table.insert(values=values))


def upgrade():
    op.create_table(
        'environment',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('networking', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_table(
        'tag',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_table(
        'category',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_category_name', 'category', ['name'])

    op.create_table(
        'apistats',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('host', sa.String(length=80), nullable=True),
        sa.Column('request_count', sa.BigInteger(), nullable=True),
        sa.Column('error_count', sa.BigInteger(), nullable=True),
        sa.Column('average_response_time', sa.Float(), nullable=True),
        sa.Column('requests_per_tenant', sa.Text(), nullable=True),
        sa.Column('requests_per_second', sa.Float(), nullable=True),
        sa.Column('errors_per_second', sa.Float(), nullable=True),
        sa.Column('cpu_count', sa.Integer(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_table(
        'instance_stats',
        sa.Column('environment_id', sa.String(length=255), nullable=False),
        sa.Column('instance_id', sa.String(length=255), nullable=False),
        sa.Column('instance_type', sa.Integer(), nullable=False),
        sa.Column('created', sa.Integer(), nullable=False),
        sa.Column('destroyed', sa.Integer(), nullable=True),
        sa.Column('type_name', sa.String(length=512), nullable=False),
        sa.Column('type_title', sa.String(length=512), nullable=True),
        sa.Column('unit_count', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('environment_id', 'instance_id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_table(
        'package',
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
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_package_fqn',
                    'package',
                    ['fully_qualified_name'])

    op.create_table(
        'session',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('environment_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('state', sa.String(length=36), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('version', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environment.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_table(
        'deployment',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('started', sa.DateTime(), nullable=False),
        sa.Column('finished', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('environment_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['environment_id'], ['environment.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_table(
        'class_definition',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name',
                  sa.String(length=128),
                  nullable=False,
                  unique=True),
        sa.Column('package_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_class_definition_name',
                    'class_definition',
                    ['name'])

    op.create_table(
        'status',
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

    op.create_table(
        'package_to_tag',
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('tag_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ondelete='CASCADE'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_table(
        'package_to_category',
        sa.Column('package_id', sa.String(length=36), nullable=False),
        sa.Column('category_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['category_id'],
                                ['category.id'],
                                ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    _create_default_categories(op)
    # end Alembic commands #


def downgrade():
    op.drop_index('ix_category_name', table_name='category')
    op.drop_index('ix_package_fqn', table_name='package')
    op.drop_index('ix_class_definition_name', table_name='class_definition')

    op.drop_table('status')
    op.drop_table('package_to_category')
    op.drop_table('class_definition')
    op.drop_table('deployment')
    op.drop_table('package_to_tag')
    op.drop_table('session')
    op.drop_table('instance_stats')
    op.drop_table('package')
    op.drop_table('apistats')
    op.drop_table('category')
    op.drop_table('tag')
    op.drop_table('environment')
    # end Alembic commands #
