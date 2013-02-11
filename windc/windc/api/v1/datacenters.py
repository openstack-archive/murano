# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

import logging

from openstack.common import wsgi

from windc import utils
from windc.core import api as core_api
from windc.db import api as db_api

LOG = logging.getLogger(__name__)


class Controller(object):
    def __init__(self, conf):
        LOG.debug("Creating data centers controller with config:"
                                                "datacenters.py %s", conf)
        self.conf = conf

    @utils.verify_tenant
    def findLBforVM(self, req, tenant_id, vm_id):
        LOG.debug("Got index request. Request: %s", req)
        result = core_api.lb_find_for_vm(self.conf, tenant_id, vm_id)
        return {'loadbalancers': result}

    @utils.verify_tenant
    def index(self, req, tenant_id):
        LOG.debug("Got index request. Request: %s", req)
        result = core_api.dc_get_index(self.conf, tenant_id)
        return {'datacenters': result}

    @utils.http_success_code(202)
    @utils.verify_tenant
    def create(self, req, tenant_id, body):
        LOG.debug("Got create request. Request: %s", req)
        #here we need to decide which device should be used
        params = body.copy()
        LOG.debug("Headers: %s", req.headers)
        # We need to create DataCenter object and return its id
        params['tenant_id'] = tenant_id
        dc_id = core_api.create_dc(self.conf, params)
        return {'datacenter': {'id': dc_id}}

    @utils.verify_tenant
    def delete(self, req, tenant_id, datacenter_id):
        LOG.debug("Got delete request. Request: %s", req)
        core_api.delete_dc(self.conf, tenant_id, datacenter_id)

    @utils.verify_tenant
    def show(self, req, tenant_id, datacenter_id):
        LOG.debug("Got datacenter info request. Request: %s", req)
        result = core_api.dc_get_data(self.conf, tenant_id, datacenter_id)
        return {'datacenter': result}

    @utils.verify_tenant
    def update(self, req, tenant_id, datacenter_id, body):
        LOG.debug("Got update request. Request: %s", req)
        core_api.update_dc(self.conf, tenant_id, datacenter_id, body)
        return {'datacenter': {'id': dc_id}}


def create_resource(conf):
    """Datacenters resource factory method"""
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    return wsgi.Resource(Controller(conf), deserializer, serializer)