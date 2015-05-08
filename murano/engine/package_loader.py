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

import abc
import os
import shutil
import sys
import tempfile
import uuid

from muranoclient.common import exceptions as muranoclient_exc
import six

from murano.common import config
from murano.common.i18n import _LE
from murano.dsl import exceptions
from murano.engine import yaql_yaml_loader
from murano.openstack.common import log as logging
from murano.packages import exceptions as pkg_exc
from murano.packages import load_utils

LOG = logging.getLogger(__name__)


class PackageLoader(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_package(self, name):
        pass

    @abc.abstractmethod
    def get_package_by_class(self, name):
        pass


class ApiPackageLoader(PackageLoader):
    def __init__(self, murano_client_factory, tenant_id):
        self._cache_directory = self._get_cache_directory()
        self._murano_client_factory = murano_client_factory
        self.tenant_id = tenant_id

    def get_package_by_class(self, name):
        filter_opts = {'class_name': name}
        try:
            package_definition = self._get_definition(filter_opts)
        except LookupError:
            exc_info = sys.exc_info()
            raise exceptions.NoPackageForClassFound(name), None, exc_info[2]
        return self._get_package_by_definition(package_definition)

    def get_package(self, name):
        filter_opts = {'fqn': name}
        try:
            package_definition = self._get_definition(filter_opts)
        except LookupError:
            exc_info = sys.exc_info()
            raise exceptions.NoPackageFound(name), None, exc_info[2]
        return self._get_package_by_definition(package_definition)

    @staticmethod
    def _get_cache_directory():
        base_directory = (
            config.CONF.packages_opts.packages_cache or
            os.path.join(tempfile.gettempdir(), 'murano-packages-cache')
        )
        directory = os.path.abspath(os.path.join(base_directory,
                                                 str(uuid.uuid4())))
        os.makedirs(directory)

        LOG.debug('Cache for package loader is located at: %s' % directory)
        return directory

    def _get_definition(self, filter_opts):
        filter_opts['catalog'] = True
        try:
            packages = list(self._murano_client_factory().packages.filter(
                **filter_opts))
            if len(packages) > 1:
                LOG.debug('Ambiguous package resolution: '
                          'more then 1 package found for query "{0}", '
                          'will resolve based on the ownership'.
                          format(filter_opts))
                return get_best_package_match(packages, self.tenant_id)
            elif len(packages) == 1:
                return packages[0]
            else:
                LOG.debug('There are no packages matching filter '
                          '{0}'.format(filter_opts))
                raise LookupError()
        except muranoclient_exc.HTTPException:
            LOG.debug('Failed to get package definition from repository')
            raise LookupError()

    def _get_package_by_definition(self, package_def):
        package_id = package_def.id
        package_name = package_def.fully_qualified_name
        package_directory = os.path.join(self._cache_directory, package_name)

        if os.path.exists(package_directory):
            try:
                return load_utils.load_from_dir(
                    package_directory, preload=True,
                    loader=yaql_yaml_loader.YaqlYamlLoader)
            except pkg_exc.PackageLoadError:
                LOG.exception(_LE(
                    'Unable to load package from cache. Clean-up...'))
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

            return load_utils.load_from_file(
                package_file.name,
                target_dir=package_directory,
                drop_dir=False,
                loader=yaql_yaml_loader.YaqlYamlLoader
            )
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

    def cleanup(self):
        shutil.rmtree(self._cache_directory, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


class DirectoryPackageLoader(PackageLoader):
    def __init__(self, base_path):
        self._base_path = base_path
        self._processed_entries = set()
        self._packages_by_class = {}
        self._packages_by_name = {}

        self._build_index()

    def get_package(self, name):
        return self._packages_by_name.get(name)

    def get_package_by_class(self, name):
        return self._packages_by_class.get(name)

    def _build_index(self):
        for entry in os.listdir(self._base_path):
            folder = os.path.join(self._base_path, entry)
            if not os.path.isdir(folder) or entry in self._processed_entries:
                continue

            try:
                package = load_utils.load_from_dir(
                    folder, preload=True,
                    loader=yaql_yaml_loader.YaqlYamlLoader)
            except pkg_exc.PackageLoadError:
                LOG.exception(_LE('Unable to load package from path: '
                                  '{0}').format(entry))
                continue

            for c in package.classes:
                self._packages_by_class[c] = package
            self._packages_by_name[package.full_name] = package

            self._processed_entries.add(entry)


def get_best_package_match(packages, tenant_id):
    public = None
    other = []
    for package in packages:
        if package.owner_id == tenant_id:
            return package
        elif package.is_public:
            public = package
        else:
            other.append(package)
    if public is not None:
        return public
    elif other:
        return other[0]
