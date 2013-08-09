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
from sqlalchemy.types import String, Text, DateTime, BigInteger


meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    environment = Table('environment', meta,
                        Column('id', String(32), primary_key=True),
                        Column('name', String(255), nullable=False),
                        Column('created', DateTime(), nullable=False),
                        Column('updated', DateTime(), nullable=False),
                        Column('tenant_id', String(32), nullable=False),
                        Column('version', BigInteger, nullable=False,
                               server_default='0'),
                        Column('description', Text(), nullable=False))
    environment.create()

    session = Table('session', meta,
                    Column('id', String(32), primary_key=True),
                    Column('environment_id', String(32), nullable=False),
                    Column('created', DateTime, nullable=False),
                    Column('updated', DateTime, nullable=False),
                    Column('user_id', String(32), nullable=False),
                    Column('version', BigInteger, nullable=False,
                           server_default='0'),
                    Column('description', Text(), nullable=True, default='{}'),
                    Column('state', Text(), nullable=False))
    session.create()

    environment = Table('environment', meta, autoload=True)
    ForeignKeyConstraint(columns=[session.c.environment_id],
                         refcolumns=[environment.c.id]).create()

    deployment = Table('deployment', meta,
                       Column('id', String(32), primary_key=True),
                       Column('environment_id', String(32), nullable=False),
                       Column('created', DateTime, nullable=False),
                       Column('updated', DateTime, nullable=False),
                       Column('started', DateTime, nullable=False),
                       Column('description', Text(), nullable=True,
                              server_default='{}'),
                       Column('finished', DateTime, nullable=True))
    deployment.create()

    environment = Table('environment', meta, autoload=True)
    ForeignKeyConstraint(columns=[deployment.c.environment_id],
                         refcolumns=[environment.c.id]).create()

    status = Table('status', meta,
                   Column('id', String(32), primary_key=True),
                   Column('created', DateTime, nullable=False),
                   Column('updated', DateTime, nullable=False),
                   Column('entity', String(10), nullable=False),
                   Column('entity_id', String(32), nullable=True),
                   Column('environment_id', String(32), nullable=True),
                   Column('deployment_id', String(32), nullable=False),
                   Column('text', Text(), nullable=False),
                   Column('details', Text(), nullable=True),
                   Column('level', String(32), nullable=False,
                          server_default='info')
                   )
    status.create()

    ForeignKeyConstraint(columns=[status.c.deployment_id],
                         refcolumns=[deployment.c.id]).create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.drop_all()
