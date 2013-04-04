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

import command
import cloud_formation
import windows_agent


class CommandDispatcher(command.CommandBase):
    def __init__(self, environment, rmqclient, token, tenant_id):
        self._command_map = {
            'cf': cloud_formation.HeatExecutor(environment, token, tenant_id),
            'agent': windows_agent.WindowsAgentExecutor(
                environment, rmqclient)
        }

    def execute(self, name, **kwargs):
        self._command_map[name].execute(**kwargs)

    def execute_pending(self):
        result = False
        for command in self._command_map.values():
            result |= command.execute_pending()

        return result

    def has_pending_commands(self):
        result = False
        for command in self._command_map.values():
            result |= command.has_pending_commands()

        return result

    def close(self):
        for t in self._command_map.values():
            t.close()
