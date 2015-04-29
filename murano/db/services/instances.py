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

from oslo_db import exception
from oslo_utils import timeutils
import sqlalchemy
from sqlalchemy.sql import func

from murano.db import models
from murano.db import session as db_session


UNCLASSIFIED = 0
APPLICATION = 100
OS_INSTANCE = 200


class InstanceStatsServices(object):
    @staticmethod
    def track_instance(instance_id, environment_id, instance_type,
                       type_name, type_title=None, unit_count=None):

        unit = db_session.get_session()
        try:
            with unit.begin():
                env = unit.query(models.Environment).get(environment_id)
                instance = models.Instance()
                instance.instance_id = instance_id
                instance.environment_id = environment_id
                instance.tenant_id = env.tenant_id
                instance.instance_type = instance_type
                instance.created = timeutils.utcnow_ts()
                instance.destroyed = None
                instance.type_name = type_name
                instance.type_title = type_title
                instance.unit_count = unit_count

                unit.add(instance)
        except exception.DBDuplicateEntry:
            unit.execute(
                sqlalchemy.update(models.Instance).where(
                    models.Instance.instance_id == instance_id and
                    models.Instance.environment_id == environment_id).values(
                        unit_count=unit_count))

    @staticmethod
    def destroy_instance(instance_id, environment_id):
        unit = db_session.get_session()
        instance = unit.query(models.Instance).get(
            (environment_id, instance_id))
        if instance and not instance.destroyed:
            instance.destroyed = timeutils.utcnow_ts()
            instance.save(unit)

    @staticmethod
    def get_aggregated_stats(environment_id):
        unit = db_session.get_session()
        now = timeutils.utcnow_ts()
        query = unit.query(models.Instance.instance_type, func.sum(
            func.coalesce(models.Instance.destroyed, now) -
            models.Instance.created), func.count()).filter(
                models.Instance.environment_id == environment_id)

        res = query.group_by(models.Instance.instance_type).all()

        return [{
                'type': int(record[0]),
                'duration': int(record[1]),
                'count': int(record[2])
                } for record in res]

    @staticmethod
    def get_raw_environment_stats(environment_id, instance_id=None):
        unit = db_session.get_session()
        now = timeutils.utcnow_ts()
        query = unit.query(models.Instance).filter(
            models.Instance.environment_id == environment_id)

        if instance_id:
            query = query.filter(models.Instance.instance_id == instance_id)

        res = query.all()

        return [{
                'type': record.instance_type,
                'duration': (record.destroyed or now) - record.created,
                'type_name': record.type_name,
                'unit_count': record.unit_count,
                'instance_id': record.instance_id,
                'type_title': record.type_title,
                'active': True if not record.destroyed else False
                } for record in res]
