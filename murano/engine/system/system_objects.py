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

import inspect

from murano.dsl import murano_class
from murano.engine.system import agent
from murano.engine.system import agent_listener
from murano.engine.system import heat_stack
from murano.engine.system import instance_reporter
from murano.engine.system import mistralclient
from murano.engine.system import net_explorer
from murano.engine.system import resource_manager
from murano.engine.system import status_reporter


def _auto_register(class_loader):
    globs = globals().copy()
    for module_name, value in globs.iteritems():
        if inspect.ismodule(value):
            for class_name in dir(value):
                class_def = getattr(value, class_name)
                if inspect.isclass(class_def) and hasattr(
                        class_def, '_murano_class_name'):
                    class_loader.import_class(class_def)


def register(class_loader, package_loader):
    _auto_register(class_loader)

    @murano_class.classname('io.murano.system.Resources')
    class ResourceManagerWrapper(resource_manager.ResourceManager):
        def initialize(self, _context):
            super(ResourceManagerWrapper, self).initialize(
                package_loader, _context)

    class_loader.import_class(agent.Agent)
    class_loader.import_class(agent_listener.AgentListener)
    class_loader.import_class(heat_stack.HeatStack)
    class_loader.import_class(mistralclient.MistralClient)
    class_loader.import_class(ResourceManagerWrapper)
    class_loader.import_class(instance_reporter.InstanceReportNotifier)
    class_loader.import_class(status_reporter.StatusReporter)
    class_loader.import_class(net_explorer.NetworkExplorer)
