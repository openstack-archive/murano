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
import tempfile
import uuid

from keystoneclient.v2_0 import client as keystoneclient
from muranoclient.common import exceptions as muranoclient_exc
from muranoclient.v1 import client as muranoclient
import six
import yaml

from muranoapi.common import config
from muranoapi.dsl import exceptions
from muranoapi.dsl import yaql_expression
from muranoapi.openstack.common import log as logging
from muranoapi.packages import application_package as app_pkg
from muranoapi.packages import exceptions as pkg_exc

LOG = logging.getLogger(__name__)


class YaqlYamlLoader(yaml.Loader):
    pass


def yaql_constructor(loader, node):
    value = loader.construct_scalar(node)
    return yaql_expression.YaqlExpression(value)

yaml.add_constructor(u'!yaql', yaql_constructor, YaqlYamlLoader)
yaml.add_implicit_resolver(u'!yaql', yaql_expression.YaqlExpression,
                           Loader=YaqlYamlLoader)


class PackageLoader(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_package(self, name):
        pass

    @abc.abstractmethod
    def get_package_by_class(self, name):
        pass


class ApiPackageLoader(PackageLoader):
    def __init__(self, token_id):
        self._cache_directory = self._get_cache_directory()
        self._client = self._get_murano_client(token_id)

    def get_package_by_class(self, name):
        filter_opts = {'class_name': name, 'limit': 1}

        try:
            package_definition = self._get_definition(filter_opts)
            return self._get_package_by_definition(package_definition)
        except(LookupError, pkg_exc.PackageLoadError):
            raise exceptions.NoPackageForClassFound(name)

    def get_package(self, name):
        filter_opts = {'fqn': name, 'limit': 1}

        try:
            package_definition = self._get_definition(filter_opts)
            return self._get_package_by_definition(package_definition)
        except(LookupError, pkg_exc.PackageLoadError):
            raise exceptions.NoPackageFound(name)

    @staticmethod
    def _get_cache_directory():
        directory = os.path.join(config.CONF.packages_cache, str(uuid.uuid4()))
        directory = os.path.abspath(directory)
        os.makedirs(directory)

        LOG.debug('Cache for package loader is located at: '
                  '{0}'.format(directory))
        return directory

    @staticmethod
    def _get_murano_client(token_id):
        murano_settings = config.CONF.murano

        endpoint_url = murano_settings.url
        if endpoint_url is None:
            keystone_settings = config.CONF.keystone
            keystone_client = keystoneclient.Client(
                endpoint=keystone_settings.auth_url,
                cacert=keystone_settings.ca_file or None,
                cert=keystone_settings.cert_file or None,
                key=keystone_settings.key_file or None,
                insecure=keystone_settings.insecure
            )

            endpoint_url = keystone_client.url_for(
                service_type='murano',
                endpoint_type=murano_settings.endpoint_type
            )

        return muranoclient.Client(
            endpoint=endpoint_url,
            key_file=murano_settings.key_file or None,
            cacert=murano_settings.cacert or None,
            cert_file=murano_settings.cert_file or None,
            insecure=murano_settings.insecure,
            token=token_id
        )

    def _get_definition(self, filter_opts):
        try:
            packages = self._client.packages.filter(**filter_opts)
            if not packages:
                LOG.debug('There are no packages matching filter '
                          '{0}'.format(filter_opts))
                # TODO(smelikyan): This exception should be replaced with one
                # defined in python-muranoclient
                raise LookupError()
            return packages[0]
        except muranoclient_exc.HTTPException:
            LOG.debug('Failed to get package definition from repository')
            raise LookupError()

    def _get_package_by_definition(self, package_def):
        package_id = package_def.id
        package_name = package_def.fully_qualified_name
        package_directory = os.path.join(self._cache_directory, package_name)

        if os.path.exists(package_directory):
            try:
                return app_pkg.load_from_dir(package_directory, preload=True,
                                             loader=YaqlYamlLoader)
            except pkg_exc.PackageLoadError:
                LOG.exception('Unable to load package from cache. Clean-up...')
                shutil.rmtree(package_directory, ignore_errors=True)

        try:
            package_data = self._client.packages.download(package_id)
        except muranoclient_exc.HTTPException:
            LOG.exception('Unable to download '
                          'package with id {0}'.format(package_id))
            raise pkg_exc.PackageLoadError()
        try:
            with tempfile.NamedTemporaryFile(delete=False) as package_file:
                package_file.write(package_data)

            return app_pkg.load_from_file(
                package_file.name,
                target_dir=package_directory,
                drop_dir=False,
                loader=YaqlYamlLoader
            )
        except IOError:
            LOG.exception('Unable to write package file')
            raise pkg_exc.PackageLoadError()
        finally:
            try:
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
                package = app_pkg.load_from_dir(folder, preload=True,
                                                loader=YaqlYamlLoader)
            except pkg_exc.PackageLoadError:
                LOG.exception('Unable to load package from path: '
                              '{0}'.format(entry))
                continue

            for c in package.classes:
                self._packages_by_class[c] = package
            self._packages_by_name[package.full_name] = package

            self._processed_entries.add(entry)
