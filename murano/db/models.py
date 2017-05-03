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
from oslo_db.sqlalchemy import models
from oslo_utils import timeutils
import sqlalchemy as sa
from sqlalchemy.ext import declarative
from sqlalchemy import orm as sa_orm

from murano.common import uuidutils
from murano.db.sqla import types as st


class TimestampMixin(object):
    __protected_attributes__ = set(["created", "updated"])

    created = sa.Column(sa.DateTime, default=timeutils.utcnow,
                        nullable=False)
    updated = sa.Column(sa.DateTime, default=timeutils.utcnow,
                        nullable=False, onupdate=timeutils.utcnow)

    def update(self, values):
        """dict.update() behaviour."""
        self.updated = timeutils.utcnow()
        super(TimestampMixin, self).update(values)

    def __setitem__(self, key, value):
        self.updated = timeutils.utcnow()
        super(TimestampMixin, self).__setitem__(key, value)


class _MuranoBase(models.ModelBase):
    def to_dict(self):
        dictionary = self.__dict__.copy()
        return dict((k, v) for k, v in dictionary.items()
                    if k != '_sa_instance_state')


Base = declarative.declarative_base(cls=_MuranoBase)


class Environment(Base, TimestampMixin):
    """Represents an Environment in the metadata-store."""
    __tablename__ = 'environment'
    __table_args__ = (sa.Index(
        'ix_name_tenant_id', 'name', 'tenant_id', unique=True),)

    id = sa.Column(sa.String(255),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(255), nullable=False)
    tenant_id = sa.Column(sa.String(36), nullable=False)
    description_text = sa.Column(sa.String(), nullable=False, default='')
    version = sa.Column(sa.BigInteger, nullable=False, default=0)
    description = sa.Column(st.JsonBlob(), nullable=False, default={})

    sessions = sa_orm.relationship("Session", backref='environment',
                                   cascade='save-update, merge, delete')

    tasks = sa_orm.relationship('Task', backref='environment',
                                cascade='save-update, merge, delete')

    cf_spaces = sa_orm.relationship("CFSpace", backref='environment',
                                    cascade='save-update, merge, delete')

    cf_serv_inst = sa_orm.relationship("CFServiceInstance",
                                       backref='environment',
                                       cascade='save-update, merge, delete')

    def to_dict(self):
        dictionary = super(Environment, self).to_dict()
        del dictionary['description']
        return dictionary


class EnvironmentTemplate(Base, TimestampMixin):
    """Represents an Environment Template in the metadata-store."""
    __tablename__ = 'environment-template'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(255), nullable=False)
    tenant_id = sa.Column(sa.String(36), nullable=False)
    description_text = sa.Column(sa.String(), nullable=False, default='')
    version = sa.Column(sa.BigInteger, nullable=False, default=0)
    description = sa.Column(st.JsonBlob(), nullable=False, default={})
    is_public = sa.Column(sa.Boolean, default=False)

    def to_dict(self):
        dictionary = super(EnvironmentTemplate, self).to_dict()
        if 'description' in dictionary:
            del dictionary['description']
        return dictionary


class Session(Base, TimestampMixin):
    __tablename__ = 'session'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    environment_id = sa.Column(sa.String(255), sa.ForeignKey('environment.id'))

    user_id = sa.Column(sa.String(64), nullable=False)
    state = sa.Column(sa.String(36), nullable=False)
    description = sa.Column(st.JsonBlob(), nullable=False)
    version = sa.Column(sa.BigInteger, nullable=False, default=0)

    def to_dict(self):
        dictionary = super(Session, self).to_dict()
        del dictionary['description']
        # object relations may be not loaded yet
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


class Task(Base, TimestampMixin):
    __tablename__ = 'task'

    id = sa.Column(sa.String(36), primary_key=True,
                   default=uuidutils.generate_uuid)
    started = sa.Column(sa.DateTime, default=timeutils.utcnow, nullable=False)
    finished = sa.Column(sa.DateTime, default=None, nullable=True)
    description = sa.Column(st.JsonBlob(), nullable=False)
    environment_id = sa.Column(sa.String(255), sa.ForeignKey('environment.id'))
    action = sa.Column(st.JsonBlob())

    statuses = sa_orm.relationship("Status", backref='task',
                                   cascade='save-update, merge, delete')
    result = sa.Column(st.JsonBlob(), nullable=True, default={})

    def to_dict(self):
        dictionary = super(Task, self).to_dict()
        if 'statuses' in dictionary:
            del dictionary['statuses']
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


class Status(Base, TimestampMixin):
    __tablename__ = 'status'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    entity_id = sa.Column(sa.String(255), nullable=True)
    entity = sa.Column(sa.String(10), nullable=True)
    task_id = sa.Column(sa.String(32), sa.ForeignKey('task.id'))
    text = sa.Column(sa.Text(), nullable=False)
    level = sa.Column(sa.String(32), nullable=False)
    details = sa.Column(sa.Text(), nullable=True)

    def to_dict(self):
        dictionary = super(Status, self).to_dict()
        # object relations may be not loaded yet
        if 'deployment' in dictionary:
            del dictionary['deployment']
        return dictionary


class ApiStats(Base, TimestampMixin):
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


package_to_category = sa.Table('package_to_category',
                               Base.metadata,
                               sa.Column('package_id',
                                         sa.String(36),
                                         sa.ForeignKey('package.id')),
                               sa.Column('category_id',
                                         sa.String(36),
                                         sa.ForeignKey('category.id',
                                                       ondelete="RESTRICT")))

package_to_tag = sa.Table('package_to_tag',
                          Base.metadata,
                          sa.Column('package_id',
                                    sa.String(36),
                                    sa.ForeignKey('package.id')),
                          sa.Column('tag_id',
                                    sa.String(36),
                                    sa.ForeignKey('tag.id',
                                                  ondelete="CASCADE")))


class Instance(Base):
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


class Package(Base, TimestampMixin):
    """Represents a meta information about application package."""
    __tablename__ = 'package'
    __table_args__ = (sa.Index('ix_package_fqn_and_owner',
                               'fully_qualified_name',
                               'owner_id', unique=True),)
    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    archive = sa.Column(st.LargeBinary())
    fully_qualified_name = sa.Column(sa.String(128),
                                     nullable=False)
    type = sa.Column(sa.String(20), nullable=False, default='class')
    author = sa.Column(sa.String(80), default='OpenStack')
    supplier = sa.Column(st.JsonBlob(), nullable=True, default={})
    name = sa.Column(sa.String(80), nullable=False)
    enabled = sa.Column(sa.Boolean, default=True)
    description = sa.Column(sa.Text(),
                            nullable=False,
                            default='The description is not provided')
    is_public = sa.Column(sa.Boolean, default=False)
    tags = sa_orm.relationship("Tag",
                               secondary=package_to_tag,
                               cascade='save-update, merge',
                               lazy='joined')
    logo = sa.Column(st.LargeBinary(), nullable=True)
    owner_id = sa.Column(sa.String(64), nullable=False)
    ui_definition = sa.Column(sa.Text)
    supplier_logo = sa.Column(sa.LargeBinary, nullable=True)
    categories = sa_orm.relationship("Category",
                                     secondary=package_to_category,
                                     cascade='save-update, merge',
                                     lazy='joined')
    class_definitions = sa_orm.relationship(
        "Class", cascade='save-update, merge, delete', lazy='joined',
        backref='package')

    def to_dict(self):
        d = self.__dict__.copy()
        not_serializable = ['_sa_instance_state',
                            'archive',
                            'logo',
                            'ui_definition',
                            'supplier_logo']
        nested_objects = ['categories', 'tags', 'class_definitions']
        for key in not_serializable:
            if key in d.keys():
                del d[key]
        for key in nested_objects:
            d[key] = [a.name for a in d.get(key, [])]
        return d


class Category(Base, TimestampMixin):
    """Represents an application categories in the datastore."""
    __tablename__ = 'category'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(80), nullable=False, index=True, unique=True)

    package_count = sa_orm.column_property(
        sa.select([sa.func.count(package_to_category.c.package_id)]).
        where(package_to_category.c.category_id == id).
        correlate_except(package_to_category)
    )

    def to_dict(self):
        d = super(Category, self).to_dict()
        d['package_count'] = self.package_count
        return d


class Tag(Base, TimestampMixin):
    """Represents tags in the datastore."""
    __tablename__ = 'tag'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(80), nullable=False, unique=True)


class Class(Base, TimestampMixin):
    """Represents a class definition in the datastore."""
    __tablename__ = 'class_definition'

    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)
    name = sa.Column(sa.String(128), nullable=False, index=True)
    package_id = sa.Column(sa.String(36), sa.ForeignKey('package.id'))


class Lock(Base):
    __tablename__ = 'locks'
    id = sa.Column(sa.String(50), primary_key=True)
    ts = sa.Column(sa.DateTime, nullable=False)


class CFOrganization(Base):
    __tablename__ = "cf_orgs"
    id = sa.Column(sa.String(255), primary_key=True)
    tenant = sa.Column(sa.String(255), nullable=False)


class CFSpace(Base):
    __tablename__ = "cf_spaces"
    id = sa.Column(sa.String(255), primary_key=True)
    environment_id = sa.Column(sa.String(255), sa.ForeignKey('environment.id'),
                               nullable=False)

    def to_dict(self):
        dictionary = super(CFSpace, self).to_dict()
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


class CFServiceInstance(Base):
    __tablename__ = 'cf_serv_inst'
    id = sa.Column(sa.String(255), primary_key=True)
    service_id = sa.Column(sa.String(255), nullable=False)
    environment_id = sa.Column(sa.String(255), sa.ForeignKey('environment.id'),
                               nullable=False)
    tenant = sa.Column(sa.String(255), nullable=False)

    def to_dict(self):
        dictionary = super(CFServiceInstance, self).to_dict()
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


def register_models(engine):
    """Creates database tables for all models with the given engine."""
    models = (Environment, Status, Session, Task,
              ApiStats, Package, Category, Class, Instance, Lock, CFSpace,
              CFOrganization)
    for model in models:
        model.metadata.create_all(engine)


def unregister_models(engine):
    """Drops database tables for all models with the given engine."""
    models = (Environment, Status, Session, Task,
              ApiStats, Package, Category, Class, Lock, CFOrganization,
              CFSpace)
    for model in models:
        model.metadata.drop_all(engine)
