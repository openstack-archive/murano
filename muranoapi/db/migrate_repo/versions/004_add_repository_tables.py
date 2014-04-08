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

from migrate.changeset import constraint

from sqlalchemy import schema
from sqlalchemy import types
meta = schema.MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    package = schema.Table(
        'package',
        meta,
        schema.Column('id',
                      types.String(32),
                      primary_key=True,
                      nullable=False),
        schema.Column('archive', types.BLOB),
        schema.Column('fully_qualified_name', types.String(512),
                      index=True, unique=True),
        schema.Column('type', types.String(20)),
        schema.Column('author', types.String(80)),
        schema.Column('name', types.String(20)),
        schema.Column('enabled', types.Boolean),
        schema.Column('description', types.String(512)),
        schema.Column('is_public', types.Boolean),
        schema.Column('logo', types.BLOB),
        schema.Column('owner_id', types.String(36)),
        schema.Column('ui_definition', types.Text),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False),
    )
    package.create()

    category = schema.Table(
        'category',
        meta,
        schema.Column('id',
                      types.String(32),
                      primary_key=True,
                      nullable=False),
        schema.Column('name',
                      types.String(80),
                      nullable=False,
                      index=True,
                      unique=True),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False),
    )
    category.create()

    package_to_category = schema.Table(
        'package_to_category',
        meta,
        schema.Column('package_id', types.String(32)),
        schema.Column('category_id', types.String(32))
    )
    package_to_category.create()

    constraint.ForeignKeyConstraint(
        columns=[package_to_category.c.package_id],
        refcolumns=[package.c.id]).create()
    constraint.ForeignKeyConstraint(
        columns=[package_to_category.c.category_id],
        refcolumns=[category.c.id]).create()

    tag = schema.Table(
        'tag',
        meta,
        schema.Column('id',
                      types.String(32),
                      primary_key=True,
                      nullable=False),
        schema.Column('name',
                      types.String(80),
                      nullable=False,
                      index=True,
                      unique=True),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False),
    )
    tag.create()

    package_to_tag = schema.Table(
        'package_to_tag',
        meta,
        schema.Column('package_id', types.String(32)),
        schema.Column('tag_id', types.String(32))
    )
    package_to_tag.create()

    constraint.ForeignKeyConstraint(
        columns=[package_to_tag.c.package_id],
        refcolumns=[package.c.id]).create()
    constraint.ForeignKeyConstraint(
        columns=[package_to_tag.c.tag_id],
        refcolumns=[tag.c.id]).create()
    class_definition = schema.Table(
        'class_definition',
        meta,
        schema.Column('id',
                      types.String(32),
                      primary_key=True,
                      nullable=False),
        schema.Column('name', types.String(80), index=True),
        schema.Column('package_id', types.String(32)),
        schema.Column('created', types.DateTime, nullable=False),
        schema.Column('updated', types.DateTime, nullable=False),
    )
    class_definition.create()

    constraint.ForeignKeyConstraint(columns=[class_definition.c.package_id],
                                    refcolumns=[package.c.id]).create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    package_to_category = schema.Table('package_to_category',
                                       meta,
                                       autoload=True)
    package_to_category.drop()
    package_to_tag = schema.Table('package_to_tag', meta, autoload=True)
    package_to_tag.drop()
    class_definition = schema.Table('class_definition', meta, autoload=True)
    class_definition.drop()
    tag = schema.Table('tag', meta, autoload=True)
    tag.drop()
    category = schema.Table('category', meta, autoload=True)
    category.drop()
    package = schema.Table('package', meta, autoload=True)
    package.drop()
