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

#from heatclient import Client
from subprocess import call

import logging
LOG = logging.getLogger(__name__)

class Heat:

	def __init__(self):
		pass

	def execute(self, command):
#		client = Client('1',OS_IMAGE_ENDPOINT, OS_TENANT_ID)
 		LOG.debug('Calling heat script to execute template')
		call(["./heat_run","stack-create","-f"+command.context['template_name'],
			command.context['stack_name']])
		pass

