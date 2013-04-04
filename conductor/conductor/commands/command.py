class CommandBase(object):
    def execute(self, **kwargs):
        pass

    def execute_pending(self):
        return False

    def has_pending_commands(self):
        return False

    def close(self):
        pass
