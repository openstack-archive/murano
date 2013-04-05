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
#    under the License.from oslo.config import cfg

from sqlalchemy.schema import MetaData, Table, Column, ForeignKey
from sqlalchemy.types import String, Text, DateTime

meta = MetaData()

session = Table('session', meta,
                Column('id', String(32), primary_key=True),
                Column('environment_id', String(32),
                       ForeignKey('environment.id')),
                Column('created', DateTime, nullable=False),
                Column('updated', DateTime, nullable=False),
                Column('user_id', String(32), nullable=False),
                Column('state', Text(), nullable=False),
                )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()
    session.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    session.drop()
