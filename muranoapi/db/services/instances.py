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

from sqlalchemy.sql import func

from muranoapi.db import models
from muranoapi.db import session as db_session
from muranoapi.openstack.common.db import exception
from muranoapi.openstack.common import timeutils


UNCLASSIFIED = 0
APPLICATION = 100
OS_INSTANCE = 200


class InstanceStatsServices(object):
    @staticmethod
    def track_instance(instance_id, environment_id, instance_type):
        instance = models.Instance()
        instance.instance_id = instance_id
        instance.environment_id = environment_id
        instance.instance_type = instance_type
        instance.created = timeutils.utcnow_ts()
        instance.destroyed = None

        unit = db_session.get_session()
        try:
            with unit.begin():
                unit.add(instance)
        except exception.DBDuplicateEntry:
            pass  # expected behaviour when record already exists

    @staticmethod
    def destroy_instance(instance_id, environment_id):
        unit = db_session.get_session()
        instance = unit.query(models.Instance).get(
            (environment_id, instance_id))
        if instance and not instance.destroyed:
            instance.destroyed = timeutils.utcnow_ts()
            instance.save(unit)

    @staticmethod
    def get_environment_stats(environment_id, instance_id=None):
        unit = db_session.get_session()
        now = timeutils.utcnow_ts()
        query = unit.query(models.Instance.instance_type, func.sum(
            func.coalesce(models.Instance.destroyed, now) -
            models.Instance.created), func.count()).filter(
                models.Instance.environment_id == environment_id)
        if instance_id is not None:
            query = query.filter(
                models.Instance.instance_id == instance_id)

        res = query.group_by(models.Instance.instance_type).all()

        return [{
                'type': int(record[0]),
                'duration': int(record[1]),
                'count': int(record[2])
                } for record in res]
