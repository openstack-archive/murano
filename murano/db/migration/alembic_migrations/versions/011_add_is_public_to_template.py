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
Add the is_public column to the environment-template for public
environment template functionality.

Revision ID: 011
Revises: table template

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.add_column('environment-template',
                  sa.Column('is_public', sa.Boolean(),
                            default=False, nullable=True))
    # end Alembic commands #


def downgrade():
    op.drop_column('environment-template', 'is_public')
    # end Alembic commands #
