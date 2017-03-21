# Copyright (c) 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import semantic_version

from oslo_config import cfg
from oslo_log import log as logging
from stevedore import dispatch


CONF = cfg.CONF
LOG = logging.getLogger(__name__)
NAMESPACE = 'io.murano.plugins.packages'


class PluginLoader(object):
    def __init__(self):
        LOG.info('Loading package type plugins')
        extension_manager = dispatch.EnabledExtensionManager(
            NAMESPACE,
            self._is_plugin_enabled,
            on_load_failure_callback=self._on_load_failure)
        self.formats = {}
        for ext in extension_manager.extensions:
            self._load_plugin(ext)

    def _load_plugin(self, extension):
        format_name = extension.entry_point.name
        self.register_format(format_name, extension.plugin)

    @staticmethod
    def _is_plugin_enabled(extension):
        if CONF.murano.enabled_plugins is None:
            # assume all plugins are enabled until manually specified otherwise
            return True
        else:
            return (extension.entry_point.dist.project_name in
                    CONF.murano.enabled_plugins)

    @staticmethod
    def _on_load_failure(manager, ep, exc):
        LOG.warning("Error loading entry-point {ep} from package {dist}: "
                    "{err}".format(ep=ep.name, dist=ep.dist, err=exc))

    @staticmethod
    def _parse_format_string(format_string):
        parts = format_string.rsplit('/', 1)
        if len(parts) != 2:
            LOG.error("Incorrect format name {name}".format(
                name=format_string))
            raise ValueError(format_string)
        return (
            parts[0].strip(),
            semantic_version.Version.coerce(parts[1])
        )

    def register_format(self, format_name, package_class):
        try:
            name, version = self._parse_format_string(format_name)
        except ValueError:
            return
        else:
            self._initialize_plugin(package_class)
            self.formats.setdefault(name, {})[version] = package_class
            LOG.info('Plugin for "{0}" package type was loaded'.format(
                format_name))

    def get_package_handler(self, format_name):
        format_name, runtime_version = self._parse_format_string(format_name)

        package_class = self.formats.get(format_name, {}).get(
            runtime_version)
        if package_class is None:
            return None
        return lambda *args, **kwargs: package_class(
            format_name, runtime_version, *args, **kwargs)

    @staticmethod
    def _initialize_plugin(plugin):
        if hasattr(plugin, "init_plugin"):
            initializer = getattr(plugin, "init_plugin")
            LOG.debug("Initializing plugin class {name}".format(name=plugin))
            initializer()
