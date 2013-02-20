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

from windc.db import api as db_api
from windc.core import change_events as events

def dc_get_index(conf, tenant_id):
	dcs = db_api.datacenter_get_all(conf, tenant_id)
	dc_list = [db_api.unpack_extra(dc) for dc in dcs]
	return dc_list
	pass

def create_dc(conf, params):
	# We need to pack all attributes which are not defined by the model explicitly
	dc_params = db_api.datacenter_pack_extra(params)
	dc = db_api.datacenter_create(conf, dc_params)
	event = events.Event(events.SCOPE_DATACENTER_CHANGE, events.ACTION_ADD)
	events.change_event(conf, event, dc)
	return dc.id
	pass

def delete_dc(conf, tenant_id, datacenter_id):
	dc = db_api.datacenter_get(conf, tenant_id, datacenter_id)
	event = events.Event(events.SCOPE_DATACENTER_CHANGE, events.ACTION_DELETE)
	events.change_event(conf, event, dc)
	db_api.datacenter_destroy(conf, datacenter_id)
	pass

def dc_get_data(conf, tenant_id, datacenter_id):
	dc = db_api.datacenter_get(conf, tenant_id, datacenter_id)
	dc_data = db_api.unpack_extra(dc)
	return dc_data
	pass

def update_dc(conf, tenant_id, datacenter_id, body):
	dc = db_api.datacenter_get(conf, tenant_id, datacenter_id)
	old_dc = copy.deepcopy(dc)
	db_api.pack_update(dc, body)
	dc = db_api.datacenter_update(conf, datacenter_id, dc)
	event = events.Event(events.SCOPE_DATACENTER_CHANGE,
                             events.ACTION_MODIFY)
	event.previous_state = old_dc
	events.change_event(conf, event, dc)
	pass

def service_get_index(conf, tenant_id, datacenter_id):
	srvcs = db_api.service_get_all_by_datacenter_id(conf, tenant_id,
                                                        datacenter_id)
	srv_list = [db_api.unpack_extra(srv) for srv in srvcs]
	return srv_list
	pass

def create_service(conf, params):
	# We need to pack all attributes which are not defined
	# by the model explicitly
	srv_params = db_api.service_pack_extra(params)
	srv = db_api.service_create(conf, srv_params)
	event = events.Event(events.SCOPE_SERVICE_CHANGE, events.ACTION_ADD)
	events.change_event(conf, event, srv)
	return srv.id
	pass

def delete_service(conf, tenant_id, datacenter_id, service_id):
	srv = db_api.service_get(conf, service_id, tenant_id)
	srv_data = db_api.unpack_extra(srv)
	event = events.Event(events.SCOPE_SERVICE_CHANGE, events.ACTION_DELETE)
	events.change_event(conf, event, srv)
	db_api.service_destroy(conf,service_id)
	pass

def service_get_data(conf, tenant_id, datacenter_id, service_id):
	srv = db_api.service_get(conf, service_id, tenant_id)
	srv_data = db_api.unpack_extra(srv)
	return srv_data
	pass

def update_service(conf, tenant_id, datacenter_id, service_id, body):
	srv = db_api.service_get(conf, service_id, tenant_id)
	old_srv = copy.deepcopy(srv)
	db_api.pack_update(srv, body)
	srv = db_api.service_update(conf, service_id, srv)
	event = events.Event(events.SCOPE_SERVICE_CHANGE, events.ACTION_MODIFY)
	event.previous_state = old_srv
	events.change_event(conf, event, srv)
	pass
