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
import uuid
LOG = logging.getLogger(__name__)

from windc.core.builder import Builder
from windc.core import change_events as events
from windc.db import api as db_api
from windc.core.templates import Template
from windc.core import commands as command_api

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

				self.submit_commands(context, event, dc)
		else:
			LOG.debug("Not in my scope. Skip event.")
		pass

	def do_analysis(self, context, event, data):
		LOG.debug("Doing analysis for data: %s", data)
		zones = data['zones']
		if data['type'] == self.type and len(zones) == 1:
			LOG.debug("It is a service which I should build.")
			datacenter_id = data['datacenter_id']
			dc = db_api.datacenter_get(context['conf'],data['tenant_id'],
					data['datacenter_id'])
			datacenter = db_api.unpack_extra(dc)
			context['stack_name']=datacenter['name']
			return True
		else:
			return False

	def plan_changes(self, context, event, data):
		# Here we can plan multiple command execution.
		# It might be Heat call command, then chef call command and other
		#
		LOG.debug("Plan changes...")
		self.prepare_template(context, event, data)
		self.chef_configuration(context, event, data)
		context['commands'].append(self.deploy_template_command(context, event, data))
		context['commands'].append(self.chef_configuration_command(context, event, data))
		pass

	def prepare_template(self, context, event, data):
		LOG.debug("Prepare CloudFormation Template...")
		template = Template()
		template.add_description('Base template for Active Directory deployment')
		sec_grp = template.create_security_group('Security group for AD')
		rule = template.create_securitygroup_rule('tcp','3389','3389','0.0.0.0/0')
		template.add_rule_to_securitygroup(sec_grp, rule)
		template.add_resource('ADSecurityGroup', sec_grp)

		instance = template.create_instance()
		instance_name= 'AD-DC001'
		template.add_security_group(instance, 'ADSecurityGroup')
		template.add_resource(instance_name, instance)

		template.add_output_value(instance_name+'-IP',{"Fn::GetAtt" : [instance_name,'PublicIp']},
			'Public IP for the domain controller.')
		context['template']=template
		pass

	def deploy_template_command(self, context, event, data):
		LOG.debug("Creating CloudFormation Template deployment command...")
		fname = "templates/"+str(uuid.uuid4())
		f=open(fname, "w")
		f.write(context['template'].to_json())
		f.close()
		context['template_name']=fname
		command = command_api.Command(command_api.TEMPLATE_DEPLOYMENT_COMMAND, context)
		return command
		pass

	def chef_configuration(self, context, event, data):
		LOG.debug("Creating Chef configuration...")
		context['Role'] = 'pdc'
		pass

	def chef_configuration_command(self, context, event, data):
		LOG.debug("Creating Chef configuration command...")
		command = command_api.Command(command_api.CHEF_COMMAND, context)
		return command

	def submit_commands(self, context, event, data):
		LOG.debug("Submit commands for execution...")
		pass