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

from oslo_db import exception
import sqlalchemy

from murano.db import cfapi_models as models
from murano.db import session as db_session


def set_tenant_for_org(cf_org_id, tenant):
    """Store tenant-org link to db"""
    unit = db_session.get_session()
    try:
        with unit.begin():
            org = models.CFOrganization()
            org.id = cf_org_id
            org.tenant = tenant
            unit.add(org)
    except exception.DBDuplicateEntry:
        unit.execute(sqlalchemy.update(models.CFOrganization).where(
            models.CFOrganization.id == cf_org_id).values(
                tenant=tenant))


def set_environment_for_space(cf_space_id, environment_id):
    """Store env-space link to db"""
    unit = db_session.get_session()
    try:
        with unit.begin():
            space = models.CFSpace()
            space.id = cf_space_id
            space.environment_id = environment_id
            unit.add(space)
    except exception.DBDuplicateEntry:
        unit.execute(sqlalchemy.update(models.CFSpace).where(
            models.CFSpace.id == cf_space_id).values(
                environment_id=environment_id))


def set_instance_for_service(instance_id, service_id, environment_id, tenant):
    """Store env-space link to db"""
    unit = db_session.get_session()
    try:
        with unit.begin():
            connection = models.CFServiceInstance()
            connection.id = instance_id
            connection.service_id = service_id
            connection.environment_id = environment_id
            connection.tenant = tenant
            unit.add(connection)
    except exception.DBDuplicateEntry:
        unit.execute(sqlalchemy.update(models.CFServiceInstance).where(
            models.CFServiceInstance.id == instance_id).values(
                environment_id=environment_id))


def get_environment_for_space(cf_space_id):
    """Take env id related to space from db"""
    unit = db_session.get_session()
    connection = unit.query(models.CFSpace).get(cf_space_id)
    return connection.environment_id


def get_tenant_for_org(cf_org_id):
    """Take tenant id related to org from db"""
    unit = db_session.get_session()
    connection = unit.query(models.CFOrganization).get(cf_org_id)
    return connection.tenant


def get_service_for_instance(instance_id):
    unit = db_session.get_session()
    connection = unit.query(models.CFServiceInstance).get(instance_id)
    return connection


def delete_environment_from_space(environment_id):
    unit = db_session.get_session()
    unit.query(models.CFSpace).filter(
        models.CFSpace.environment_id == environment_id).delete()
