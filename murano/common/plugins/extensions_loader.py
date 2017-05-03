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

import inspect
import re

from oslo_config import cfg
from oslo_log import log as logging
from stevedore import dispatch

from murano.dsl import murano_package


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

# regexp validator to ensure that the entry-point name is a valid MuranoPL
# class name with an optional namespace name
NAME_RE = re.compile(r'^[a-zA-Z]\w*(\.[a-zA-Z]\w*)*$')


class PluginLoader(object):
    def __init__(self, namespace="io.murano.extensions"):
        LOG.info('Loading extension plugins')
        self.namespace = namespace
        extension_manager = dispatch.EnabledExtensionManager(
            self.namespace,
            PluginLoader.is_plugin_enabled,
            on_load_failure_callback=PluginLoader._on_load_failure)
        self.packages = {}
        name_map = {}
        for ext in extension_manager.extensions:
            self.load_extension(ext, name_map)
        self.cleanup_duplicates(name_map)

    def load_extension(self, extension, name_map):
        dist_name = str(extension.entry_point.dist)
        name = extension.entry_point.name
        if not NAME_RE.match(name):
            LOG.warning("Entry-point 'name' {name} is invalid".format(
                name=name))
            return
        name_map.setdefault(name, []).append(dist_name)
        if dist_name in self.packages:
            package = self.packages[dist_name]
        else:
            package = PackageDefinition(extension.entry_point.dist)
            self.packages[dist_name] = package

        plugin = extension.plugin
        try:
            package.classes[name] = initialize_plugin(plugin)
        except Exception:
            LOG.exception("Unable to initialize plugin for {name}".format(
                name=name))
            return
        LOG.info("Loaded class {class_name} from {dist}".format(
                 class_name=name, dist=dist_name))

    def cleanup_duplicates(self, name_map):
        for class_name, package_names in name_map.items():
            if len(package_names) >= 2:
                LOG.warning("Class is defined in multiple packages!")
                for package_name in package_names:
                    LOG.warning(
                        "Disabling class {class_name} in {dist} due to "
                        "conflict".format(
                            class_name=class_name, dist=package_name))
                    self.packages[package_name].classes.pop(class_name)

    @staticmethod
    def is_plugin_enabled(extension):
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

    def register_in_loader(self, package_loader):
        for package in self.packages.values():
            package_loader.register_package(
                MuranoPackage(package_loader, package))


def initialize_plugin(plugin):
    if hasattr(plugin, "init_plugin"):
        initializer = getattr(plugin, "init_plugin")
        if inspect.ismethod(initializer) and initializer.__self__ is plugin:
            LOG.debug("Initializing plugin class {name}".format(name=plugin))
            initializer()
    return plugin


class PackageDefinition(object):
    def __init__(self, distribution):
        self.name = distribution.project_name
        self.version = distribution.version
        if distribution.has_metadata(distribution.PKG_INFO):
            # This has all the package metadata, including Author,
            # description, License etc
            self.info = distribution.get_metadata(distribution.PKG_INFO)
        else:
            self.info = None
        self.classes = {}


class MuranoPackage(murano_package.MuranoPackage):
    def __init__(self, pkg_loader, package_definition):
        super(MuranoPackage, self).__init__(
            pkg_loader, package_definition.name, runtime_version='1.0')
        for class_name, clazz in package_definition.classes.items():
            if hasattr(clazz, "_murano_class_name"):
                LOG.warning("Class '%(class_name)s' has a MuranoPL "
                            "name '%(name)s' defined which will be "
                            "ignored" %
                            dict(class_name=class_name,
                                 name=getattr(clazz, "_murano_class_name")))
            LOG.debug("Registering '%s' from '%s' in class loader",
                      class_name, package_definition.name)
            self.register_class(clazz, class_name)

    def get_resource(self, name):
        raise NotImplementedError()
