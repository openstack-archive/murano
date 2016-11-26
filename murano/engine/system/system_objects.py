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

from murano.engine.system import agent
from murano.engine.system import agent_listener
from murano.engine.system import heat_stack
from murano.engine.system import instance_reporter
from murano.engine.system import logger
from murano.engine.system import metadef_browser
from murano.engine.system import net_explorer
from murano.engine.system import project
from murano.engine.system import resource_manager
from murano.engine.system import status_reporter
from murano.engine.system import test_fixture
from murano.engine.system import user
from murano.engine.system import workflowclient


def register(package):
    package.register_class(agent.Agent)
    package.register_class(agent_listener.AgentListener)
    package.register_class(heat_stack.HeatStack)
    package.register_class(resource_manager.ResourceManager)
    package.register_class(instance_reporter.InstanceReportNotifier)
    package.register_class(status_reporter.StatusReporter)
    package.register_class(net_explorer.NetworkExplorer)
    package.register_class(logger.Logger)
    package.register_class(test_fixture.TestFixture)
    package.register_class(workflowclient.MistralClient)
    package.register_class(metadef_browser.MetadefBrowser)
    package.register_class(user.User)
    package.register_class(project.Project)
