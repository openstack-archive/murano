import command
import cloud_formation
import windows_agent


class CommandDispatcher(command.CommandBase):
    def __init__(self, environment_id, rmqclient, token):
        self._command_map = {
            'cf': cloud_formation.HeatExecutor(environment_id, token),
            'agent': windows_agent.WindowsAgentExecutor(
                environment_id, rmqclient)
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
