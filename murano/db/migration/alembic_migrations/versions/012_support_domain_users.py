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
Change sizes of columns that hold keystone user ID to support domain users
which are 64 characters long.

Revision ID: 012
Revises: table session, table package

"""

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'

from alembic import op
import sqlalchemy as sa


MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.alter_column('session', 'user_id', type_=sa.String(64), nullable=False)
    op.alter_column('package', 'owner_id', type_=sa.String(64), nullable=False)
    # end Alembic commands #


def downgrade():
    op.alter_column('package', 'owner_id', type_=sa.String(36), nullable=False)
    op.alter_column('session', 'user_id', type_=sa.String(36), nullable=False)
    # end Alembic commands #
