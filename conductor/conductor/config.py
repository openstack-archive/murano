from ConfigParser import SafeConfigParser


class Config(object):
    CONFIG_PATH = './etc/app.config'

    def __init__(self, filename=None):
        self.config = SafeConfigParser()
        self.config.read(filename or self.CONFIG_PATH)

    def get_setting(self, section, name, default=None):
        if not self.config.has_option(section, name):
            return default
        return self.config.get(section, name)

    def __getitem__(self, item):
        parts = item.rsplit('.', 1)
        return self.get_setting(
            parts[0] if len(parts) == 2 else 'DEFAULT', parts[-1])
