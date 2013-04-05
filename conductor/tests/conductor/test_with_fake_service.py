# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from conductor.app import ConductorWorkflowService
from conductor.openstack.common import service

class TestMethodsAndClasses(unittest.TestCase):

    def test_init_service_class(self):
        launcher = service.ServiceLauncher()
        con = ConductorWorkflowService()
        launcher.launch_service(con)
        
