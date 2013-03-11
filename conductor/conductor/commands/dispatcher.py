import command
import cloud_formation
import windows_agent


class CommandDispatcher(command.CommandBase):
    def __init__(self, environment_name, rmqclient):
        self._command_map = {
            'cf': cloud_formation.HeatExecutor(environment_name),
            'agent': windows_agent.WindowsAgentExecutor(
                environment_name, rmqclient)
        }

    def execute(self, name, **kwargs):
        self._command_map[name].execute(**kwargs)

    def execute_pending(self, callback):
        result = 0
        count = [0]

        def on_result():
            count[0] -= 1
            if not count[0]:
                callback()

        for command in self._command_map.values():
            count[0] += 1
            result += 1
            if not command.execute_pending(on_result):
                count[0] -= 1
                result -= 1

        return result > 0


    def has_pending_commands(self):
        result = False
        for command in self._command_map.values():
            result |= command.has_pending_commands()

        return result

    def close(self):
        for t in self._command_map.values():
            t.close()
