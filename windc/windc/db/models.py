# vim: tabstop=4 shiftwidth=4 softtabstop=4

#Copyright by Mirantis Inc.
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
"""SQLAlchemy models for balancer data."""

import datetime
import uuid

from sqlalchemy.orm import relationship, backref
from sqlalchemy import (Column, ForeignKey, Integer, String, Boolean,
                        DateTime)

from windc.db.base import Base, DictBase, JsonBlob


def create_uuid():
    return uuid.uuid4().hex


class DataCenter(DictBase, Base):
    """
    Represents a data center - a Windows Environment with different
    services in it.
    """

    __tablename__ = 'datacenter'
    id = Column(String(32), primary_key=True, default=create_uuid)
    name = Column(String(255))
    type = Column(String(255))
    version = Column(String(255))
    tenant_id = Column(String(100))
    KMS = Column(String(80))
    WSUS = Column(String(80))
    extra = Column(JsonBlob())


class Service(DictBase, Base):
    """
    Represents an instance of service.

    :var name: string
    :var type: string - type of service (e.g. Active Directory)
    :var tenant_id: string - OpenStack tenant ID
    :var extra: dictionary - additional attributes
    """

    __tablename__ = 'service'
    id = Column(String(32), primary_key=True, default=create_uuid)
    datacenter_id = Column(String(32), ForeignKey('datacenter.id'))
    name = Column(String(255))
    type = Column(String(40))
    status = Column(String(40))
    tenant_id = Column(String(40))
    created_at = Column(DateTime, default=datetime.datetime.utcnow,
                        nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow,
                        nullable=False)
    deployed = Column(String(40))
    vm_id = Column(String(40))
    extra = Column(JsonBlob())
    datacenter = relationship(DataCenter,
                          backref=backref('service', order_by=id),
                          uselist=False)

def register_models(engine):
    """Create tables for models."""

    Base.metadata.create_all(engine)
