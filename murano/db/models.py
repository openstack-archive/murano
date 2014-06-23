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

"""
SQLAlchemy models for murano data
"""
import anyjson

import sqlalchemy as sa
from sqlalchemy.ext import compiler as sa_compiler
from sqlalchemy.ext import declarative as sa_decl
from sqlalchemy import orm as sa_orm

from murano.common import uuidutils
from murano.db import session as db_session
from murano.openstack.common import timeutils


BASE = sa_decl.declarative_base()


@sa_compiler.compiles(sa.BigInteger, 'sqlite')
def compile_big_int_sqlite(type_, compiler, **kw):
    return 'INTEGER'


class ModelBase(object):
    def save(self, session=None):
        """Save this object"""
        session = session or db_session.get_session()
        session.add(self)
        session.flush()

    def update(self, values):
        """dict.update() behaviour."""
        for k, v in values.iteritems():
            self[k] = v

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        self._i = iter(sa_orm.object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def to_dict(self):
        dictionary = self.__dict__.copy()
        return dict((k, v) for k, v in dictionary.iteritems()
                    if k != '_sa_instance_state')


class ModificationsTrackedObject(ModelBase):
    __protected_attributes__ = set(["created", "updated"])

    created = sa.Column(sa.DateTime, default=timeutils.utcnow,
                        nullable=False)
    updated = sa.Column(sa.DateTime, default=timeutils.utcnow,
                        nullable=False, onupdate=timeutils.utcnow)

    def update(self, values):
        """dict.update() behaviour."""
        self.updated = timeutils.utcnow()
        super(ModificationsTrackedObject, self).update(values)

    def __setitem__(self, key, value):
        self.updated = timeutils.utcnow()
        super(ModificationsTrackedObject, self).__setitem__(key, value)


class JsonBlob(sa.TypeDecorator):
    impl = sa.Text

    def process_bind_param(self, value, dialect):
        return anyjson.serialize(value)

    def process_result_value(self, value, dialect):
        return anyjson.deserialize(value)


class Environment(BASE, ModificationsTrackedObject):
    """Represents a Environment in the metadata-store"""
    __tablename__ = 'environment'

    id = sa.Column(sa.String(255),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(255), nullable=False)
    tenant_id = sa.Column(sa.String(36), nullable=False)
    version = sa.Column(sa.BigInteger, nullable=False, default=0)
    description = sa.Column(JsonBlob(), nullable=False, default={})
    networking = sa.Column(JsonBlob(), nullable=True, default={})

    sessions = sa_orm.relationship("Session", backref='environment',
                                   cascade='save-update, merge, delete')
    deployments = sa_orm.relationship("Deployment", backref='environment',
                                      cascade='save-update, merge, delete')

    def to_dict(self):
        dictionary = super(Environment, self).to_dict()
        del dictionary['description']
        return dictionary


class Session(BASE, ModificationsTrackedObject):
    __tablename__ = 'session'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    environment_id = sa.Column(sa.String(255), sa.ForeignKey('environment.id'))

    user_id = sa.Column(sa.String(36), nullable=False)
    state = sa.Column(sa.String(36), nullable=False)
    description = sa.Column(JsonBlob(), nullable=False)
    version = sa.Column(sa.BigInteger, nullable=False, default=0)

    def to_dict(self):
        dictionary = super(Session, self).to_dict()
        del dictionary['description']
        #object relations may be not loaded yet
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


class Deployment(BASE, ModificationsTrackedObject):
    __tablename__ = 'deployment'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    started = sa.Column(sa.DateTime, default=timeutils.utcnow, nullable=False)
    finished = sa.Column(sa.DateTime, default=None, nullable=True)
    description = sa.Column(JsonBlob(), nullable=False)
    environment_id = sa.Column(sa.String(255), sa.ForeignKey('environment.id'))

    statuses = sa_orm.relationship("Status", backref='deployment',
                                   cascade='save-update, merge, delete')

    def to_dict(self):
        dictionary = super(Deployment, self).to_dict()
        # del dictionary["description"]
        if 'statuses' in dictionary:
            del dictionary['statuses']
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


class Status(BASE, ModificationsTrackedObject):
    __tablename__ = 'status'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    entity_id = sa.Column(sa.String(255), nullable=True)
    entity = sa.Column(sa.String(10), nullable=True)
    deployment_id = sa.Column(sa.String(36), sa.ForeignKey('deployment.id'))
    text = sa.Column(sa.String(), nullable=False)
    level = sa.Column(sa.String(32), nullable=False)
    details = sa.Column(sa.Text(), nullable=True)

    def to_dict(self):
        dictionary = super(Status, self).to_dict()
        #object relations may be not loaded yet
        if 'deployment' in dictionary:
            del dictionary['deployment']
        return dictionary


class ApiStats(BASE, ModificationsTrackedObject):
    __tablename__ = 'apistats'

    id = sa.Column(sa.Integer(), primary_key=True)
    host = sa.Column(sa.String(80))
    request_count = sa.Column(sa.BigInteger())
    error_count = sa.Column(sa.BigInteger())
    average_response_time = sa.Column(sa.Float())
    requests_per_tenant = sa.Column(sa.Text())
    requests_per_second = sa.Column(sa.Float())
    errors_per_second = sa.Column(sa.Float())
    cpu_count = sa.Column(sa.Integer())
    cpu_percent = sa.Column(sa.Float())

    def to_dict(self):
        dictionary = super(ApiStats, self).to_dict()
        return dictionary

package_to_category = sa.Table('package_to_category',
                               BASE.metadata,
                               sa.Column('package_id',
                                         sa.String(36),
                                         sa.ForeignKey('package.id')),
                               sa.Column('category_id',
                                         sa.String(36),
                                         sa.ForeignKey('category.id',
                                                       ondelete="RESTRICT")))

package_to_tag = sa.Table('package_to_tag',
                          BASE.metadata,
                          sa.Column('package_id',
                                    sa.String(36),
                                    sa.ForeignKey('package.id')),
                          sa.Column('tag_id',
                                    sa.String(36),
                                    sa.ForeignKey('tag.id',
                                    ondelete="CASCADE")))


class Instance(BASE, ModelBase):
    __tablename__ = 'instance_stats'

    environment_id = sa.Column(
        sa.String(255), primary_key=True, nullable=False)
    instance_id = sa.Column(
        sa.String(255), primary_key=True, nullable=False)
    instance_type = sa.Column(sa.Integer, default=0, nullable=False)
    created = sa.Column(sa.Integer, nullable=False)
    destroyed = sa.Column(sa.Integer, nullable=True)
    type_name = sa.Column('type_name', sa.String(512), nullable=False)
    type_title = sa.Column('type_title', sa.String(512))
    unit_count = sa.Column('unit_count', sa.Integer())
    tenant_id = sa.Column('tenant_id', sa.String(36), nullable=False)

    def to_dict(self):
        dictionary = super(Instance, self).to_dict()
        return dictionary


class Package(BASE, ModificationsTrackedObject):
    """
    Represents a meta information about application package.
    """
    __tablename__ = 'package'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    archive = sa.Column(sa.LargeBinary)
    fully_qualified_name = sa.Column(sa.String(512),
                                     nullable=False,
                                     index=True,
                                     unique=True)
    type = sa.Column(sa.String(20), nullable=False, default='class')
    author = sa.Column(sa.String(80), default='Openstack')
    name = sa.Column(sa.String(80), nullable=False)
    enabled = sa.Column(sa.Boolean, default=True)
    description = sa.Column(sa.String(512),
                            nullable=False,
                            default='The description is not provided')
    is_public = sa.Column(sa.Boolean, default=True)
    tags = sa_orm.relationship("Tag",
                               secondary=package_to_tag,
                               cascade='save-update, merge',
                               lazy='joined')
    logo = sa.Column(sa.LargeBinary, nullable=True)
    owner_id = sa.Column(sa.String(36), nullable=False)
    ui_definition = sa.Column(sa.Text)
    categories = sa_orm.relationship("Category",
                                     secondary=package_to_category,
                                     cascade='save-update, merge',
                                     lazy='joined')
    class_definitions = sa_orm.relationship(
        "Class", cascade='save-update, merge, delete', lazy='joined')

    def to_dict(self):
        d = self.__dict__.copy()
        not_serializable = ['_sa_instance_state',
                            'archive',
                            'logo',
                            'ui_definition']
        nested_objects = ['categories', 'tags', 'class_definitions']
        for key in not_serializable:
            if key in d.keys():
                del d[key]
        for key in nested_objects:
            d[key] = [a.name for a in d.get(key, [])]
        return d


class Category(BASE, ModificationsTrackedObject):
    """
    Represents an application categories in the datastore.
    """
    __tablename__ = 'category'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(80), nullable=False, index=True, unique=True)


class Tag(BASE, ModificationsTrackedObject):
    """
    Represents tags in the datastore.
    """
    __tablename__ = 'tag'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(80), nullable=False, unique=True)


class Class(BASE, ModificationsTrackedObject):
    """
    Represents a class definition in the datastore.
    """
    __tablename__ = 'class_definition'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(512), nullable=False, index=True)
    package_id = sa.Column(sa.String(36), sa.ForeignKey('package.id'))


def register_models(engine):
    """
    Creates database tables for all models with the given engine
    """
    models = (Environment, Status, Session, Deployment,
              ApiStats, Package, Category, Class, Instance)
    for model in models:
        model.metadata.create_all(engine)


def unregister_models(engine):
    """
    Drops database tables for all models with the given engine
    """
    models = (Environment, Status, Session, Deployment,
              ApiStats, Package, Category, Class)
    for model in models:
        model.metadata.drop_all(engine)
