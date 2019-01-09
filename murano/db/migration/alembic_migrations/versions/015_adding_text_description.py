# Copyright 2016 OpenStack Foundation.
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

"""Increase time resolution for status reports

Revision ID: 015
Create Date: 2016-06-17

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.add_column('environment', sa.Column('description_text', sa.Text(),
                  nullable=True))
    op.add_column('environment-template', sa.Column('description_text',
                                                    sa.Text(),
                  nullable=True))


def downgrade():
    with op.batch_alter_table("environment") as batch_op:
        batch_op.drop_column('description_text')
    with op.batch_alter_table("environment-template") as batch_op2:
        batch_op2.drop_column('description_text')
