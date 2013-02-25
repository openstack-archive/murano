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

from windc.core import builder_set
from windc.core import builder
from windc.drivers import command_executor
#Declare events types

SCOPE_SERVICE_CHANGE = "Service"
SCOPE_DATACENTER_CHANGE = "Datacenter"
SCOPE_VM_CHANGE = "VMChange"

ACTION_ADD = "Add"
ACTION_MODIFY = "Modify"
ACTION_DELETE = "Delete"

class Event:
    scope = None
    action = None
    previous_state = None
    def __init__(self, scope, action):
        self.scope = scope
        self.action = action

def change_event(conf, event, data):
    LOG.info("Change event of type: %s ", event)
    context = builder.create_context()
    context['conf'] = conf
    executor = command_executor.Executor(conf)
    for builder_type in builder_set.builders.set:
        builder_instance = builder_set.builders.set[builder_type]
        builder_instance.build(context, event, data, executor)





