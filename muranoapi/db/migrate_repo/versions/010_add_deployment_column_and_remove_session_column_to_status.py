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
from sqlalchemy.types import String

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    status = Table('status', meta, autoload=True)
    environment = Table('environment', meta, autoload=True)
    session = Table('session', meta, autoload=True)
    deployment = Table('deployment', meta, autoload=True)

    deployment_id = Column('deployment_id', String(32), nullable=False)
    deployment_id.create(status)
    ForeignKeyConstraint(columns=[status.c.deployment_id],
                         refcolumns=[deployment.c.id]).create()

    ForeignKeyConstraint(columns=[status.c.environment_id],
                         refcolumns=[environment.c.id]).drop()
    status.c.environment_id.drop()
    ForeignKeyConstraint(columns=[status.c.session_id],
                         refcolumns=[session.c.id]).drop()
    status.c.session_id.drop()
    status.c.entity.alter(nullable=True)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    status = Table('status', meta, autoload=True)
    environment = Table('environment', meta, autoload=True)
    session = Table('session', meta, autoload=True)
    deployment = Table('deployment', meta, autoload=True)

    ForeignKeyConstraint(columns=[status.c.deployment_id],
                         refcolumns=[deployment.c.id]).drop()
    status.c.deployment_id.drop()

    environment_id = Column('environment_id', String(32), nullable=False)
    environment_id.create(status)
    ForeignKeyConstraint(columns=[status.c.environment_id],
                         refcolumns=[environment.c.id]).create()

    session_id = Column('session_id', String(32), nullable=False)
    session_id.create(status)
    ForeignKeyConstraint(columns=[status.c.session_id],
                         refcolumns=[session.c.id]).create()

    status.c.entity.alter(nullable=False)
