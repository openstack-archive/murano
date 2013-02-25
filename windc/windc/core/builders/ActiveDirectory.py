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
import os
from sphinx.ext.autosummary import generate

LOG = logging.getLogger(__name__)

from windc.core.builder import Builder
from windc.core import change_events as events
from windc.db import api as db_api
from windc.core.templates import Template
from windc.core import commands as command_api
import json
from windc.common import cfg
from random import choice

chars = 'abcdefghklmnopqrstvwxyz2345689'


class ActiveDirectory(Builder):
    def __init__(self, conf):
        self.name = "Active Directory Builder"
        self.type = "active_directory_service"
        self.version = 1
        self.conf = conf

        conf.register_group(cfg.OptGroup(name="rabbitmq"))
        conf.register_opts([
            cfg.StrOpt('host', default='10.0.0.1'),
            cfg.StrOpt('vhost', default='keero'),
        ], group="rabbitmq")


    def build(self, context, event, data, executor):
        dc = db_api.unpack_extra(data)
        if event.scope == events.SCOPE_SERVICE_CHANGE:
            LOG.info ("Got service change event. Analysing..")
            if self.do_analysis(context, event, dc):
                self.plan_changes(context, event, dc)

                self.submit_commands(context, event, dc, executor)
        else:
            LOG.debug("Not in my scope. Skip event.")
        pass

    def generate(self, length):
        return ''.join(choice(chars) for _ in range(length))

    def do_analysis(self, context, event, data):
        LOG.debug("Doing analysis for data: %s", data)
        print data

        context['zones'] = ['a1']
        if data['type'] == self.type:
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
        # self.chef_configuration(context, event, data)
        # context['commands'].append(self.deploy_template_command(context, event, data))
        # context['commands'].append(self.chef_configuration_command(context, event, data))
        pass

    def prepare_template(self, context, event, data):
        LOG.debug("Prepare CloudFormation Template...")
        # template = Template()
        # template.add_description('Base template for Active Directory deployment')
        # sec_grp = template.create_security_group('Security group for AD')
        # rule = template.create_securitygroup_rule('tcp','3389','3389','0.0.0.0/0')
        # template.add_rule_to_securitygroup(sec_grp, rule)
        # template.add_resource('ADSecurityGroup', sec_grp)
        #
        # instance = template.create_instance()
        # instance_name= 'AD-DC001'
        # template.add_security_group(instance, 'ADSecurityGroup')
        # template.add_resource(instance_name, instance)
        #
        # template.add_output_value(instance_name+'-IP',{"Fn::GetAtt" : [instance_name,'PublicIp']},
        # 	'Public IP for the domain controller.')

        print "-------------------"
        print data
        print "-------------------"
        print context
        print "********"
        try:
            print self.conf.rabbitmq.vhost
        except Exception, ex:
            print ex
        print "********"

        with open('data/Windows.template', 'r') as f:
            read_data = f.read()

        template = json.loads(read_data)

        instance_template = template['Resources']['InstanceTemplate']

        del template['Resources']['InstanceTemplate']
        context['instances'] = []
        context['template_arguments'] = {
            "KeyName": "keero-linux-keys",
            "InstanceType": "m1.medium",
            "ImageName": "ws-2012-full-agent"
        }

        for i in range(data['dc_count']):
            instance_name = 'dc' + str(i) + "x" + self.generate(9)
            context['instances'].append(instance_name)
            template['Resources'][instance_name] = instance_template

        context['template']=template
        pass

    def deploy_template_command(self, context, event, data, executor):
        LOG.debug("Creating CloudFormation Template deployment command...")
        #print context['template'].to_json()
        LOG.debug(context['template'])
        if not os.path.exists("templates"):
            os.mkdir("templates")
        fname = "templates/"+str(uuid.uuid4())
        print "Saving template to", fname
        f=open(fname, "w")
        f.write(json.dumps(context['template']))
        f.close()
        context['template_name']=fname
        command = command_api.Command(command_api.TEMPLATE_DEPLOYMENT_COMMAND, context)
        executor.execute(command)

    def chef_configuration(self, context, event, data):
        LOG.debug("Creating Chef configuration...")
        context['Role'] = 'pdc'
        pass

    def transform(self, path, map):
        with open(path, 'r') as f:
            read_data = f.read()

        template = json.loads(read_data)
        if 'Commands' in template:
            for command in template['Commands']:
                if 'Arguments' in command:
                    for argument, argument_value in command['Arguments'].items():
                        if isinstance(argument_value, (str, unicode)) and argument_value.startswith("@"):
                            command['Arguments'][argument] = map[argument_value[1:]]

        return json.dumps(template)

    def deploy_execution_plan(self, context, event, data, executor):
        i = 0
        for instance in context['instances']:
            i += 1
            if i == 1:
                files = ["data/CreatePrimaryDC.json"]
            else:
                files = []

            for file in files:
                queueData = {
                    "queueName" : str("%s-%s" % (context['stack_name'], instance)),
                    "resultQueueName": "-execution-results",
                    "body": self.transform(file, data)
                }
                command = command_api.Command(command_api.EXECUTION_PLAN_DEPLOYMENT_COMMAND, context, queueData)
                executor.execute(command)




    def chef_configuration_command(self, context, event, data):
        LOG.debug("Creating Chef configuration command...")
        command = command_api.Command(command_api.CHEF_COMMAND, context)
        return command

    def submit_commands(self, context, event, data, executor):
        LOG.debug("Submit commands for execution...")
        self.deploy_template_command(context, event, data, executor)
        self.deploy_execution_plan(context, event, data, executor)
        print "Commands submitted"
        pass
