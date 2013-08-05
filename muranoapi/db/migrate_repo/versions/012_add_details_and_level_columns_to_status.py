#    Copyright (c) 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import Text, String

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    status = Table('status', meta, autoload=True)
    details = Column('details', Text(), nullable=True)
    level = Column('level', String(32), nullable=False, server_default='info')

    details.create(status)
    level.create(status)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    status = Table('status', meta, autoload=True)
    status.c.details.drop()
    status.c.level.drop()
