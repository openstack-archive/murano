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
from migrate.changeset.constraint import ForeignKeyConstraint

from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import String, Text, DateTime

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    status = Table('status', meta,
                   Column('id', String(32), primary_key=True),
                   Column('created', DateTime, nullable=False),
                   Column('updated', DateTime, nullable=False),
                   Column('entity', String(10), nullable=False),
                   Column('environment_id', String(32), nullable=False),
                   Column('session_id', String(32), nullable=False),
                   Column('text', Text(), nullable=False),
                   )
    status.create()

    environment = Table('environment', meta, autoload=True)
    ForeignKeyConstraint(columns=[status.c.environment_id],
                         refcolumns=[environment.c.id]).create()
    session = Table('session', meta, autoload=True)
    ForeignKeyConstraint(columns=[status.c.session_id],
                         refcolumns=[session.c.id]).create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    status = Table('status', meta, autoload=True)
    status.drop()
