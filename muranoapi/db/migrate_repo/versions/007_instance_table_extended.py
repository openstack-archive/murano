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

from sqlalchemy import schema
from sqlalchemy import types

meta = schema.MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    table = schema.Table('instance', meta, autoload=True)
    table.drop()
    table = schema.Table(
        'instance_stats',
        meta,
        schema.Column('environment_id', types.String(100), primary_key=True),
        schema.Column('instance_id', types.String(100), primary_key=True),
        schema.Column('instance_type', types.Integer, nullable=False),
        schema.Column('created', types.Integer, nullable=False),
        schema.Column('destroyed', types.Integer, nullable=True),
        schema.Column('type_name', types.String(512), nullable=False),
        schema.Column('type_title', types.String(512)),
        schema.Column('unit_count', types.Integer()),
        schema.Column('tenant_id', types.String(32), nullable=False))
    table.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    table = schema.Table('instance_stats', meta, autoload=True)
    table.rename('instance')
    table.c.type_name.drop()
    table.c.type_title.drop()
    table.c.unit_count.drop()
    table.c.tenant_id.drop()
