#    Copyright (c) 2014 Mirantis, Inc.
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
import uuid

from muranoapi.common import consts
from muranoapi.openstack.common import timeutils

meta = schema.MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    table = schema.Table('category', meta, autoload=True)
    for category in consts.CATEGORIES:
        now = timeutils.utcnow()
        values = {'id': uuid.uuid4().hex, 'name': category, 'updated': now,
                  'created': now}
        table.insert(values=values).execute()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    table = schema.Table('category', meta, autoload=True)
    for category in consts.CATEGORIES:
        table.delete().where(table.c.name == category).execute()
