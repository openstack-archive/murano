# Copyright (c) 2014 Mirantis Inc.
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

import os
import os.path
import shutil
import sys
import tempfile
import uuid

from muranoclient.common import exceptions as muranoclient_exc
from oslo_config import cfg
from oslo_log import log as logging

from murano.common.i18n import _LE, _LI
from murano.dsl import constants
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import package_loader
from murano.engine import murano_package
from murano.engine.system import system_objects
from murano.engine import yaql_yaml_loader
from murano.packages import exceptions as pkg_exc
from murano.packages import load_utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ApiPackageLoader(package_loader.MuranoPackageLoader):
    def __init__(self, murano_client_factory, tenant_id, root_loader=None):
        self._cache_directory = self._get_cache_directory()
        self._murano_client_factory = murano_client_factory
        self.tenant_id = tenant_id
        self._class_cache = {}
        self._package_cache = {}
        self._root_loader = root_loader or self

    def load_class_package(self, class_name, version_spec):
        packages = self._class_cache.get(class_name)
        if packages:
            version = version_spec.select(packages.iterkeys())
            if version:
                return packages[version]

        filter_opts = {'class_name': class_name,
                       'version': helpers.breakdown_spec_to_query(
                           version_spec)}
        try:
            package_definition = self._get_definition(filter_opts)
        except LookupError:
            exc_info = sys.exc_info()
            raise (exceptions.NoPackageForClassFound(class_name),
                   None, exc_info[2])
        return self._to_dsl_package(
            self._get_package_by_definition(package_definition))

    def load_package(self, package_name, version_spec):
        packages = self._package_cache.get(package_name)
        if packages:
            version = version_spec.select(packages.iterkeys())
            if version:
                return packages[version]

        filter_opts = {'fqn': package_name,
                       'version': helpers.breakdown_spec_to_query(
                           version_spec)}
        try:
            package_definition = self._get_definition(filter_opts)
        except LookupError:
            exc_info = sys.exc_info()
            raise exceptions.NoPackageFound(package_name), None, exc_info[2]
        return self._to_dsl_package(
            self._get_package_by_definition(package_definition))

    def register_package(self, package):
        for name in package.classes:
            self._class_cache.setdefault(name, {})[package.version] = package
        self._package_cache.setdefault(package.name, {})[
            package.version] = package

    @staticmethod
    def _get_cache_directory():
        base_directory = (
            CONF.packages_opts.packages_cache or
            os.path.join(tempfile.gettempdir(), 'murano-packages-cache')
        )
        directory = os.path.abspath(os.path.join(base_directory,
                                                 uuid.uuid4().hex))
        os.makedirs(directory)

        LOG.debug('Cache for package loader is located at: {dir}'.format(
            dir=directory))
        return directory

    def _get_definition(self, filter_opts):
        filter_opts['catalog'] = True
        try:
            packages = list(self._murano_client_factory().packages.filter(
                **filter_opts))
            if len(packages) > 1:
                LOG.debug('Ambiguous package resolution: more then 1 package '
                          'found for query "{opts}", will resolve based on the'
                          ' ownership'.format(opts=filter_opts))
                return self._get_best_package_match(packages)
            elif len(packages) == 1:
                return packages[0]
            else:
                LOG.debug('There are no packages matching filter '
                          '{opts}'.format(opts=filter_opts))
                raise LookupError()
        except muranoclient_exc.HTTPException:
            LOG.debug('Failed to get package definition from repository')
            raise LookupError()

    def _to_dsl_package(self, app_package):
        dsl_package = murano_package.MuranoPackage(
            self._root_loader, app_package)
        for name in app_package.classes:
            dsl_package.register_class(
                (lambda cls: lambda: get_class(app_package, cls))(name),
                name)
        if app_package.full_name == constants.CORE_LIBRARY:
            system_objects.register(dsl_package)
        self.register_package(dsl_package)
        return dsl_package

    def _get_package_by_definition(self, package_def):
        package_id = package_def.id
        package_directory = os.path.join(self._cache_directory, package_id)

        if os.path.exists(package_directory):
            try:
                return load_utils.load_from_dir(package_directory)
            except pkg_exc.PackageLoadError:
                LOG.error(_LE('Unable to load package from cache. Clean-up.'))
                shutil.rmtree(package_directory, ignore_errors=True)
        try:
            package_data = self._murano_client_factory().packages.download(
                package_id)
        except muranoclient_exc.HTTPException as e:
            msg = 'Error loading package id {0}: {1}'.format(
                package_id, str(e)
            )
            exc_info = sys.exc_info()
            raise pkg_exc.PackageLoadError(msg), None, exc_info[2]
        package_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as package_file:
                package_file.write(package_data)

            with load_utils.load_from_file(
                    package_file.name,
                    target_dir=package_directory,
                    drop_dir=False) as app_package:
                return app_package
        except IOError:
            msg = 'Unable to extract package data for %s' % package_id
            exc_info = sys.exc_info()
            raise pkg_exc.PackageLoadError(msg), None, exc_info[2]
        finally:
            try:
                if package_file:
                    os.remove(package_file.name)
            except OSError:
                pass

    def _get_best_package_match(self, packages):
        public = None
        other = []
        for package in packages:
            if package.owner_id == self.tenant_id:
                return package
            elif package.is_public:
                public = package
            else:
                other.append(package)
        if public is not None:
            return public
        elif other:
            return other[0]

    def cleanup(self):
        shutil.rmtree(self._cache_directory, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


class DirectoryPackageLoader(package_loader.MuranoPackageLoader):
    def __init__(self, base_path, root_loader=None):
        self._base_path = base_path
        self._packages_by_class = {}
        self._packages_by_name = {}
        self._loaded_packages = set()
        self._root_loader = root_loader or self
        self._build_index()

    def _build_index(self):
        for folder in self.search_package_folders(self._base_path):
            try:
                package = load_utils.load_from_dir(folder)
                dsl_package = murano_package.MuranoPackage(
                    self._root_loader, package)
                for class_name in package.classes:
                    dsl_package.register_class(
                        (lambda pkg, cls:
                            lambda: get_class(pkg, cls))(package, class_name),
                        class_name
                    )
                if dsl_package.name == constants.CORE_LIBRARY:
                    system_objects.register(dsl_package)
                self.register_package(dsl_package)
            except pkg_exc.PackageLoadError:
                LOG.info(_LI('Unable to load package from path: {0}').format(
                    folder))
                continue
            LOG.info(_LI('Loaded package from path {0}').format(folder))

    def load_class_package(self, class_name, version_spec):
        packages = self._packages_by_class.get(class_name)
        if not packages:
            raise exceptions.NoPackageForClassFound(class_name)
        version = version_spec.select(packages.iterkeys())
        if not version:
            raise exceptions.NoPackageForClassFound(class_name)
        return packages[version]

    def load_package(self, package_name, version_spec):
        packages = self._packages_by_name.get(package_name)
        if not packages:
            raise exceptions.NoPackageFound(package_name)
        version = version_spec.select(packages.iterkeys())
        if not version:
            raise exceptions.NoPackageFound(package_name)
        return packages[version]

    def register_package(self, package):
        for c in package.classes:
            self._packages_by_class.setdefault(c, {})[
                package.version] = package
        self._packages_by_name.setdefault(package.name, {})[
            package.version] = package

    @property
    def packages(self):
        for package_versions in self._packages_by_name.itervalues():
            for package in package_versions.itervalues():
                yield package

    @staticmethod
    def split_path(path):
        tail = True
        while tail:
            path, tail = os.path.split(path)
            if tail:
                yield path

    @classmethod
    def search_package_folders(cls, path):
        packages = set()
        for folder, _, files in os.walk(path):
            if 'manifest.yaml' in files:
                found = False
                for part in cls.split_path(folder):
                    if part in packages:
                        found = True
                        break
                if not found:
                    packages.add(folder)
                    yield folder


class CombinedPackageLoader(package_loader.MuranoPackageLoader):
    def __init__(self, murano_client_factory, tenant_id, root_loader=None):
        root_loader = root_loader or self
        self.api_loader = ApiPackageLoader(
            murano_client_factory, tenant_id, root_loader)
        self.directory_loaders = []

        for folder in CONF.engine.load_packages_from:
            if os.path.exists(folder):
                self.directory_loaders.append(DirectoryPackageLoader(
                    folder, root_loader))

    def load_package(self, package_name, version_spec):
        for loader in self.directory_loaders:
            try:
                return loader.load_package(package_name, version_spec)
            except exceptions.NoPackageFound:
                continue
        return self.api_loader.load_package(
            package_name, version_spec)

    def load_class_package(self, class_name, version_spec):
        for loader in self.directory_loaders:
            try:
                return loader.load_class_package(class_name, version_spec)
            except exceptions.NoPackageForClassFound:
                continue
        return self.api_loader.load_class_package(
            class_name, version_spec)

    def register_package(self, package):
        self.api_loader.register_package(package)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.api_loader.cleanup()
        return False


def get_class(package, name):
    version = package.runtime_version
    loader = yaql_yaml_loader.get_loader(version)
    contents, file_id = package.get_class(name)
    return loader(contents, file_id)
