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
SQLAlchemy models for muranoapi data
"""
import anyjson

from sqlalchemy import Column, String, BigInteger, TypeDecorator, ForeignKey
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime, Text
from sqlalchemy.orm import relationship, object_mapper
from muranoapi.common import uuidutils

from muranoapi.openstack.common import timeutils
from muranoapi.db.session import get_session

BASE = declarative_base()


@compiles(BigInteger, 'sqlite')
def compile_big_int_sqlite(type_, compiler, **kw):
    return 'INTEGER'


class ModelBase(object):
    __protected_attributes__ = set(["created", "updated"])

    created = Column(DateTime, default=timeutils.utcnow,
                     nullable=False)
    updated = Column(DateTime, default=timeutils.utcnow,
                     nullable=False, onupdate=timeutils.utcnow)

    def save(self, session=None):
        """Save this object"""
        session = session or get_session()
        session.add(self)
        session.flush()

    def update(self, values):
        """dict.update() behaviour."""
        self.updated = timeutils.utcnow()
        for k, v in values.iteritems():
            self[k] = v

    def __setitem__(self, key, value):
        self.updated = timeutils.utcnow()
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
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


class JsonBlob(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return anyjson.serialize(value)

    def process_result_value(self, value, dialect):
        return anyjson.deserialize(value)


class Environment(BASE, ModelBase):
    """Represents a Environment in the metadata-store"""
    __tablename__ = 'environment'

    id = Column(String(32), primary_key=True, default=uuidutils.generate_uuid)
    name = Column(String(255), nullable=False)
    tenant_id = Column(String(32), nullable=False)
    version = Column(BigInteger, nullable=False, default=0)
    description = Column(JsonBlob(), nullable=False, default={})
    networking = Column(JsonBlob(), nullable=True, default={})

    sessions = relationship("Session", backref='environment',
                            cascade='save-update, merge, delete')
    deployments = relationship("Deployment", backref='environment',
                               cascade='save-update, merge, delete')

    def to_dict(self):
        dictionary = super(Environment, self).to_dict()
        del dictionary['description']
        return dictionary


class Session(BASE, ModelBase):
    __tablename__ = 'session'

    id = Column(String(32), primary_key=True, default=uuidutils.generate_uuid)
    environment_id = Column(String(32), ForeignKey('environment.id'))

    user_id = Column(String(36), nullable=False)
    state = Column(String(36), nullable=False)
    description = Column(JsonBlob(), nullable=False)
    version = Column(BigInteger, nullable=False, default=0)

    def to_dict(self):
        dictionary = super(Session, self).to_dict()
        del dictionary['description']
        #object relations may be not loaded yet
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


class Deployment(BASE, ModelBase):
    __tablename__ = 'deployment'

    id = Column(String(32), primary_key=True, default=uuidutils.generate_uuid)
    started = Column(DateTime, default=timeutils.utcnow, nullable=False)
    finished = Column(DateTime, default=None, nullable=True)
    description = Column(JsonBlob(), nullable=False)
    environment_id = Column(String(32), ForeignKey('environment.id'))

    statuses = relationship("Status", backref='deployment',
                            cascade='save-update, merge, delete')

    def to_dict(self):
        dictionary = super(Deployment, self).to_dict()
        # del dictionary["description"]
        if 'statuses' in dictionary:
            del dictionary['statuses']
        if 'environment' in dictionary:
            del dictionary['environment']
        return dictionary


class Status(BASE, ModelBase):
    __tablename__ = 'status'

    id = Column(String(32), primary_key=True, default=uuidutils.generate_uuid)
    entity_id = Column(String(32), nullable=True)
    entity = Column(String(10), nullable=True)
    deployment_id = Column(String(32), ForeignKey('deployment.id'))
    text = Column(String(), nullable=False)
    level = Column(String(32), nullable=False)
    details = Column(Text(), nullable=True)

    def to_dict(self):
        dictionary = super(Status, self).to_dict()
        #object relations may be not loaded yet
        if 'deployment' in dictionary:
            del dictionary['deployment']
        return dictionary


def register_models(engine):
    """
    Creates database tables for all models with the given engine
    """
    models = (Environment, Status, Session, Deployment)
    for model in models:
        model.metadata.create_all(engine)


def unregister_models(engine):
    """
    Drops database tables for all models with the given engine
    """
    models = (Environment, Status, Session, Deployment)
    for model in models:
        model.metadata.drop_all(engine)
