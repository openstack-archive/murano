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

Revision ID: 002
Revises: None
Create Date: 2014-06-23 16:34:33.698760

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.add_column(
        'package',
        sa.Column('supplier_logo', sa.types.LargeBinary)
    )
    op.add_column(
        'package',
        sa.Column('supplier', sa.types.Text())
    )
    # end Alembic commands #


def downgrade():
    op.drop_column('package', 'supplier')
    op.drop_column('package', 'supplier_logo')
    # end Alembic commands #
