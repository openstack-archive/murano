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
SQLAlchemy models for service broker data
"""
from oslo_db.sqlalchemy import models
import sqlalchemy as sa
from sqlalchemy.ext import declarative


class _ServiceBrokerBase(models.ModelBase):
    pass


Base = declarative.declarative_base(cls=_ServiceBrokerBase)


class CFOrganization(Base):
    __tablename__ = "cf_orgs"
    id = sa.Column(sa.String(255), primary_key=True)
    tenant = sa.Column(sa.String(255), nullable=False)


class CFSpace(Base):
    __tablename__ = "cf_spaces"

    id = sa.Column(sa.String(255), primary_key=True)
    environment_id = sa.Column(sa.String(255), nullable=False)


class CFServiceInstance(Base):
    __tablename__ = 'cf_serv_inst'

    id = sa.Column(sa.String(255), primary_key=True)
    service_id = sa.Column(sa.String(255), nullable=False)
    environment_id = sa.Column(sa.String(255), nullable=False)
    tenant = sa.Column(sa.String(255), nullable=False)


def register_models(engine):
    """Creates database tables for all models with the given engine."""
    models = (CFSpace, CFOrganization, CFServiceInstance)
    for model in models:
        model.metadata.create_all(engine)


def unregister_models(engine):
    """Drops database tables for all models with the given engine."""
    models = (CFOrganization, CFSpace, CFServiceInstance)
    for model in models:
        model.metadata.drop_all(engine)
