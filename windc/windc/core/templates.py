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
from windc.common.wsgi import JSONResponseSerializer
LOG = logging.getLogger(__name__)

class Template:
	def __init__(self):
		self.content = {'AWSTemplateFormatVersion':'2010-09-09', 'Description':'',
			'Parameters':{}}
		self.content['Mappings'] = {
			"AWSInstanceType2Arch" : {
			  "t1.micro"    : { "Arch" : "32" },
			  "m1.small"    : { "Arch" : "32" },
			  "m1.large"    : { "Arch" : "64" },
			  "m1.xlarge"   : { "Arch" : "64" },
			  "m2.xlarge"   : { "Arch" : "64" },
			  "m2.2xlarge"  : { "Arch" : "64" },
			  "m2.4xlarge"  : { "Arch" : "64" },
			  "c1.medium"   : { "Arch" : "32" },
			  "c1.xlarge"   : { "Arch" : "64" },
			  "cc1.4xlarge" : { "Arch" : "64" }
			},
			"DistroArch2AMI": {
			  "F16"     : { "32" : "F16-i386-cfntools", "64" : "F16-x86_64-cfntools" },
			  "F17"     : { "32" : "F17-i386-cfntools", "64" : "F17-x86_64-cfntools" },
			  "U10"     : { "32" : "U10-i386-cfntools", "64" : "U10-x86_64-cfntools" },
			  "RHEL-6.1": { "32" : "rhel61-i386-cfntools", "64" : "rhel61-x86_64-cfntools" },
			  "RHEL-6.2": { "32" : "rhel62-i386-cfntools", "64" : "rhel62-x86_64-cfntools" },
			  "RHEL-6.3": { "32" : "rhel63-i386-cfntools", "64" : "rhel63-x86_64-cfntools" }
			}
		  }
		self.content['Resources'] = {}
		self.content['Outputs'] = {}

	def to_json(self):
		serializer = JSONResponseSerializer()
		json = serializer.to_json(self.content)
		return json


	def empty_template(self):
		pass

	def add_description(self, description):
		self.content['Description'] = description

	def add_parameter(self, name, parameter):
		self.content['Parameters'].update({name : parameter})

	def add_resource(self, name, resource):
		self.content['Resources'].update({name : resource})

	def create_parameter(self, defult, type, decription):
		parameter = {'Default':default, 'Type':type, 'Description':description}
		return parameter

	def create_security_group(self, description):
		sec_grp = {'Type':'AWS::EC2::SecurityGroup'}
		sec_grp['Properties'] = {}
		sec_grp['Properties']['GroupDescription'] = description
		sec_grp['Properties']['SecurityGroupIngress'] = []
		return sec_grp

	def add_rule_to_securitygroup(self, grp, rule):
		grp['Properties']['SecurityGroupIngress'].append(rule)

	def create_securitygroup_rule(self, proto, f_port, t_port, cidr):
		rule = {'IpProtocol':proto, 'FromPort':f_port, 'ToPort':t_port,'CidrIp': cidr}
		return rule

	def create_instance(self):
		instance = {'Type':'AWS::EC2::Instance','Metadata':{},'Properties':{}}
		instance['Properties']['ImageId'] = 'U10-x86_64-cfntools'
		instance['Properties']['SecurityGroups']=[]
		instance['Properties']['KeyName'] = 'keero-linux-keys'
		instance['Properties']['InstanceType'] = 'm1.small'
		return instance

	def add_security_group(self, instance, grp_name):
		instance['Properties']['SecurityGroups'].append({'Ref': grp_name})

	def add_output_value(self, name, value, description):
		self.content['Outputs'].update({name:{'Value':value, 'Description':description}})

	def get_content(self):
		return self.content




