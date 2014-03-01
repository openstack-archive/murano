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
    stats = schema.Table(
        'apistats',
        meta,
        schema.Column('id', types.Integer(), primary_key=True),
        schema.Column('host', types.String(80)),
        schema.Column('request_count', types.BigInteger()),
        schema.Column('error_count', types.BigInteger()),
        schema.Column('average_response_time', types.Float()),
        schema.Column('requests_per_tenant', types.Text()),
        schema.Column('requests_per_second', types.Float()),
        schema.Column('errors_per_second', types.Float()),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False))
    stats.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    stats = schema.Table('apistats', meta, autoload=True)
    stats.drop()
