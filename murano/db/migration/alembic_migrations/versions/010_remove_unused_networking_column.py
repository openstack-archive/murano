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
Revision ID: 010
Revises: None
Create Date: 2015-09-08 00:00:00.698760

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    with op.batch_alter_table("environment") as batch_op:
        batch_op.drop_column('networking')
    with op.batch_alter_table("environment-template") as batch_op2:
        batch_op2.drop_column('networking')


def downgrade():
    op.add_column('environment', sa.Column('networking', sa.Text(),
                  nullable=True))
    op.add_column('environment-template', sa.Column('networking', sa.Text(),
                  nullable=True))
