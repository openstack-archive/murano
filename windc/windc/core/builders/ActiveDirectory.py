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
LOG = logging.getLogger(__name__)

from windc.core.builder import Builder
from windc.core import change_events as events
from windc.db import api as db_api

class ActiveDirectory(Builder):
	def __init__(self):
		self.name = "Active Directory Builder"
		self.type = "active_directory_service"
		self.version = 1

	def build(self, context, event, data):
		dc = db_api.unpack_extra(data)
		if event.scope == events.SCOPE_SERVICE_CHANGE:
			LOG.info ("Got service change event. Analysing..")
			if self.do_analysis(context, event, dc):
				self.plan_changes(context, event, dc)
		else:
			LOG.debug("Not in my scope. Skip event.")
		pass

	def do_analysis(self, context, event, data):
		LOG.debug("Doing analysis for data: %s", data)
		zones = data['zones']
		if data['type'] == self.type and len(zones) == 1:
			LOG.debug("It is a service which I should build.")
			return True
		else:
			return False

	def plan_changes(self, context, event, data):
		pass

