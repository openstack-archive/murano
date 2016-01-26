# Copyright (c) 2014 Mirantis, Inc.
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

from alembic import op
import six
import sqlalchemy as sa


def transform_table(name, renames, defaults, *columns, **kw):
    def escape(val):
        if isinstance(val, six.string_types):
            return "'{0}'".format(val)
        elif val is None:
            return 'NULL'
        else:
            return val

    engine = op.get_bind()
    meta = sa.MetaData(bind=engine)
    meta.reflect()
    new_name = name + '__tmp'
    old_table = meta.tables[name]
    mapping = dict(
        (renames.get(col.name, col.name), col.name) for col in old_table.c
    )

    columns_to_select = [
        old_table.c[mapping[c.name]]
        if c.name in mapping else escape(defaults.get(c.name))
        for c in columns if isinstance(c, sa.Column)
    ]
    select_as = [
        c.name for c in columns if isinstance(c, sa.Column)
    ]
    select = sa.sql.select(columns_to_select)

    op.create_table(new_name, *columns, **kw)
    meta.reflect()
    new_table = meta.tables[new_name]
    insert = sa.sql.insert(new_table)
    if engine.dialect.dialect_description == 'postgresql+psycopg2':
        insert = insert.returning(next(iter(new_table.primary_key.columns)))
    insert = insert.from_select(select_as, select)
    engine.execute(insert)
    op.drop_table(name)
    op.rename_table(new_name, name)
