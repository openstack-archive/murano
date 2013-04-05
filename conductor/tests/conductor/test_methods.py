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
import conductor.rabbitmq as rabbitmq
from conductor.workflow import Workflow
import conductor.xml_code_engine as engine

class TestMethodsAndClasses(unittest.TestCase):

    def test_init_service_class(self):
        con = ConductorWorkflowService()

        con.start()
        con.stop()
