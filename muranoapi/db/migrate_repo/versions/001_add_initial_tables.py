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
from migrate.changeset import constraint as const

from sqlalchemy import schema
from sqlalchemy import types


meta = schema.MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()

    environment = schema.Table(
        'environment',
        meta,
        schema.Column('id', types.String(32), primary_key=True),
        schema.Column('name', types.String(255), nullable=False),
        schema.Column('created', types.DateTime(), nullable=False),
        schema.Column('updated', types.DateTime(), nullable=False),
        schema.Column('tenant_id', types.String(32), nullable=False),
        schema.Column('version', types.BigInteger, nullable=False,
                      server_default='0'),
        schema.Column('description', types.Text(), nullable=False))
    environment.create()

    session = schema.Table(
        'session',
        meta,
        schema.Column('id', types.String(32), primary_key=True),
        schema.Column('environment_id', types.String(32), nullable=False),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False),
        schema.Column('user_id', types.String(32), nullable=False),
        schema.Column('version', types.BigInteger, nullable=False,
                      server_default='0'),
        schema.Column('description', types.Text(), nullable=True),
        schema.Column('state', types.Text(), nullable=False))
    session.create()

    environment = schema.Table('environment', meta, autoload=True)
    const.ForeignKeyConstraint(columns=[session.c.environment_id],
                               refcolumns=[environment.c.id]).create()

    deployment = schema.Table(
        'deployment',
        meta,
        schema.Column('id', types.String(32), primary_key=True),
        schema.Column('environment_id', types.String(32), nullable=False),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False),
        schema.Column('started', types.DateTime, nullable=False),
        schema.Column('description', types.Text(), nullable=True),
        schema.Column('finished', types.DateTime, nullable=True))
    deployment.create()

    environment = schema.Table('environment', meta, autoload=True)
    const.ForeignKeyConstraint(columns=[deployment.c.environment_id],
                               refcolumns=[environment.c.id]).create()

    status = schema.Table(
        'status',
        meta,
        schema.Column('id', types.String(32), primary_key=True),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False),
        schema.Column('entity', types.String(10), nullable=True),
        schema.Column('entity_id', types.String(32), nullable=True),
        schema.Column('environment_id', types.String(32), nullable=True),
        schema.Column('deployment_id', types.String(32), nullable=False),
        schema.Column('text', types.Text(), nullable=False),
        schema.Column('details', types.Text(), nullable=True),
        schema.Column('level', types.String(32), nullable=False,
                      server_default='info'))
    status.create()

    const.ForeignKeyConstraint(columns=[status.c.deployment_id],
                               refcolumns=[deployment.c.id]).create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.drop_all()
