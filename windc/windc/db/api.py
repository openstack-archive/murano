# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
# All Rights Reserved.
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
"""Database storage API."""

import functools
import datetime

from windc.db import models
from windc.db.session import get_session
from windc import exception



# XXX(akscram): pack_ and unpack_ are helper methods to compatibility
def pack_extra(model, values):
    obj_ref = model()
    pack_update(obj_ref, values)
    return obj_ref


def unpack_extra(obj_ref):
    obj_dict = dict(obj_ref.iteritems())
    obj_dict.update(obj_dict.pop('extra', None) or {})
    return obj_dict


def pack_update(obj_ref, values):
    obj_dict = values.copy()
    for k, v in values.iteritems():
        if k in obj_ref.keys():
            obj_ref[k] = obj_dict.pop(k)
    if obj_dict:
        if obj_ref['extra'] is not None:
            obj_ref['extra'].update(obj_dict)
        else:
            obj_ref['extra'] = obj_dict.copy()


datacenter_pack_extra = functools.partial(pack_extra, models.DataCenter)
service_pack_extra = functools.partial(pack_extra, models.Service)


# Datacenter


def datacenter_get(conf, datacenter_id, session=None):
    session = session or get_session(conf)
    datacenter_ref = session.query(models.DataCenter).\
                         filter_by(id=datacenter_id).first()
    if not datacenter_ref:
        raise exception.DeviceNotFound(datacenter_id=datacenter_id)
    return datacenter_ref


def datacenter_get_all(conf):
    session = get_session(conf)
    query = session.query(models.DataCenter)
    return query.all()


def datacenter_create(conf, values):
    session = get_session(conf)
    with session.begin():
        datacenter_ref = models.DataCenter()
        datacenter_ref.update(values)
        session.add(datacenter_ref)
        return datacenter_ref


def datacenter_update(conf, datacenter_id, values):
    session = get_session(conf)
    with session.begin():
        datacenter_ref = datacenter_get(conf, datacenter_id, session=session)
        datacenter_ref.update(values)
        return datacenter_ref


def datacenter_destroy(conf, datacenter_id):
    session = get_session(conf)
    with session.begin():
        datacenter_ref = device_get(conf, datacenter_id, session=session)
        session.delete(datacenter_ref)

# Service


def service_get(conf, service_id, tenant_id=None, session=None):
    session = session or get_session(conf)
    query = session.query(models.Service).filter_by(id=service_id)
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    service_ref = query.first()
    if not service_ref:
        raise exception.ServiceNotFound(service_ref=service_ref)
    return service_ref


def service_get_all_by_project(conf, tenant_id):
    session = get_session(conf)
    query = session.query(models.Service).filter_by(tenant_id=tenant_id)
    return query.all()


def service_get_all_by_vm_id(conf, tenant_id, vm_id):
    session = get_session(conf)
    query = session.query(models.Service).distinct().\
                    filter_by(tenant_id=tenant_id).\
                    filter(vm_id == vm_id)
    return query.all()


def service_get_all_by_datacenter_id(conf, datacenter_id):
    session = get_session(conf)
    query = session.query(models.Service).filter_by(datacenter_id=datacenter_id)
    service_refs = query.all()
    if not service_refs:
        raise exception.ServiceNotFound('No service '
                                             'for the datacenter %s found'
                                             % datacenter_id)
    return service_refs


def service_create(conf, values):
    session = get_session(conf)
    with session.begin():
        service_ref = models.Service()
        service_ref.update(values)
        session.add(service_ref)
        return service_ref


def service_update(conf, service_id, values):
    session = get_session(conf)
    with session.begin():
        service_ref = service_get(conf, service_id, session=session)
        service_ref.update(values)
        service_ref['updated_at'] = datetime.datetime.utcnow()
        return service_ref


def service_destroy(conf, service_id):
    session = get_session(conf)
    with session.begin():
        service_ref = service_get(conf, service_id, session=session)
        session.delete(service_ref)


def service_count_active_by_datacenter(conf, datacenter_id):
    session = get_session(conf)
    with session.begin():
        service_count = session.query(models.Service).\
                                  filter_by(datacenter_id=datacenter_id).\
                                  filter_by(status=service_status.ACTIVE).\
                                  count()
        return service_count


