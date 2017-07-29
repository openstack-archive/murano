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

import collections
import itertools
import os
import os.path
import shutil
import sys
import tempfile
import uuid

import eventlet
from muranoclient.common import exceptions as muranoclient_exc
from muranoclient.glance import client as glare_client
import muranoclient.v1.client as muranoclient
from oslo_config import cfg
from oslo_log import log as logging
from oslo_log import versionutils
from oslo_utils import fileutils
import six

from murano.common import auth_utils
from murano.dsl import constants
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import package_loader
from murano.engine import murano_package
from murano.engine.system import system_objects
from murano.engine import yaql_yaml_loader
from murano.packages import exceptions as pkg_exc
from murano.packages import load_utils
from murano import utils as m_utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

download_mem_locks = collections.defaultdict(m_utils.ReaderWriterLock)
usage_mem_locks = collections.defaultdict(m_utils.ReaderWriterLock)


class ApiPackageLoader(package_loader.MuranoPackageLoader):
    def __init__(self, execution_session, root_loader=None):
        self._cache_directory = self._get_cache_directory()
        self._class_cache = {}
        self._package_cache = {}
        self._root_loader = root_loader or self
        self._execution_session = execution_session
        self._last_glare_token = None
        self._glare_client = None
        self._murano_client = None
        self._murano_client_session = None

        self._mem_locks = []
        self._ipc_locks = []
        self._downloaded = []
        self._fixations = collections.defaultdict(set)
        self._new_fixations = collections.defaultdict(set)

    def _get_glare_client(self):
        glare_settings = CONF.glare
        session = auth_utils.get_client_session(self._execution_session)
        token = session.auth.get_token(session)
        if self._last_glare_token != token:
            self._last_glare_token = token
            self._glare_client = None

        if self._glare_client is None:
            url = glare_settings.url
            if not url:
                url = session.get_endpoint(
                    service_type='artifact',
                    interface=glare_settings.endpoint_type,
                    region_name=CONF.home_region)
            # TODO(gyurco): use auth_utils.get_session_client_parameters
            self._glare_client = glare_client.Client(
                endpoint=url, token=token,
                insecure=glare_settings.insecure,
                key_file=glare_settings.keyfile or None,
                ca_file=glare_settings.cafile or None,
                cert_file=glare_settings.certfile or None,
                type_name='murano',
                type_version=1)
        return self._glare_client

    @property
    def client(self):
        last_glare_client = self._glare_client
        if CONF.engine.packages_service in ['glance', 'glare']:
            if CONF.engine.packages_service == 'glance':
                versionutils.report_deprecated_feature(
                    LOG, "'glance' packages_service option has been renamed "
                         "to 'glare', please update your configuration")
            artifacts_client = self._get_glare_client()
        else:
            artifacts_client = None
        if artifacts_client != last_glare_client:
            self._murano_client = None
        if not self._murano_client:
            parameters = auth_utils.get_session_client_parameters(
                service_type='application-catalog',
                execution_session=self._execution_session,
                conf='murano'
            )
            self._murano_client = muranoclient.Client(
                artifacts_client=artifacts_client, **parameters)
        return self._murano_client

    def load_class_package(self, class_name, version_spec):
        packages = self._class_cache.get(class_name)
        if packages:
            version = version_spec.select(packages.keys())
            if version:
                return packages[version]

        filter_opts = {'class_name': class_name,
                       'version': helpers.breakdown_spec_to_query(
                           version_spec)}
        try:
            package_definition = self._get_definition(filter_opts)
            self._lock_usage(package_definition)
        except LookupError:
            exc_info = sys.exc_info()
            six.reraise(exceptions.NoPackageForClassFound,
                        exceptions.NoPackageForClassFound(class_name),
                        exc_info[2])
        return self._to_dsl_package(
            self._get_package_by_definition(package_definition))

    def load_package(self, package_name, version_spec):
        fixed_versions = self._fixations[package_name]
        version = version_spec.select(fixed_versions)
        if version:
            version_spec = helpers.parse_version_spec(version)

        packages = self._package_cache.get(package_name)
        if packages:
            version = version_spec.select(packages.keys())
            if version:
                return packages[version]

        filter_opts = {'fqn': package_name,
                       'version': helpers.breakdown_spec_to_query(
                           version_spec)}
        try:
            package_definition = self._get_definition(filter_opts)
            self._lock_usage(package_definition)
        except LookupError:
            exc_info = sys.exc_info()
            six.reraise(exceptions.NoPackageFound,
                        exceptions.NoPackageFound(package_name),
                        exc_info[2])
        else:
            package = self._get_package_by_definition(package_definition)
            self._fixations[package_name].add(package.version)
            self._new_fixations[package_name].add(package.version)
            return self._to_dsl_package(package)

    def register_package(self, package):
        for name in package.classes:
            self._class_cache.setdefault(name, {})[package.version] = package
        self._package_cache.setdefault(package.name, {})[
            package.version] = package

    @staticmethod
    def _get_cache_directory():
        base_directory = (
            CONF.engine.packages_cache or
            os.path.join(tempfile.gettempdir(), 'murano-packages-cache')
        )

        if CONF.engine.enable_packages_cache:
            directory = os.path.abspath(base_directory)
        else:
            directory = os.path.abspath(os.path.join(base_directory,
                                                     uuid.uuid4().hex))

        if not os.path.isdir(directory):
            fileutils.ensure_tree(directory)

        LOG.debug('Cache for package loader is located at: {dir}'.format(
            dir=directory))
        return directory

    def _get_definition(self, filter_opts):
        filter_opts['catalog'] = True
        try:
            packages = list(self.client.packages.filter(
                **filter_opts))
            if len(packages) > 1:
                LOG.debug('Ambiguous package resolution: more than 1 package '
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
        package_directory = os.path.join(
            self._cache_directory,
            package_def.fully_qualified_name,
            getattr(package_def, 'version', '0.0.0'),
            package_id)

        if os.path.isdir(package_directory):
            try:
                return load_utils.load_from_dir(package_directory)
            except pkg_exc.PackageLoadError:
                LOG.exception('Unable to load package from cache. Clean-up.')
                shutil.rmtree(package_directory, ignore_errors=True)

        # the package is not yet in cache, let's try to download it.
        download_lock_path = os.path.join(
            self._cache_directory, '{}_download.lock'.format(package_id))
        download_ipc_lock = m_utils.ExclusiveInterProcessLock(
            path=download_lock_path, sleep_func=eventlet.sleep)

        with download_mem_locks[package_id].write_lock(), download_ipc_lock:

            # NOTE(kzaitsev):
            # in case there were 2 concurrent threads/processes one might have
            # already downloaded this package. Check before trying to download
            if os.path.isdir(package_directory):
                try:
                    return load_utils.load_from_dir(package_directory)
                except pkg_exc.PackageLoadError:
                    LOG.error('Unable to load package from cache. Clean-up.')
                    shutil.rmtree(package_directory, ignore_errors=True)

            # attempt the download itself
            try:
                LOG.debug("Attempting to download package {} {}".format(
                    package_def.fully_qualified_name, package_id))
                package_data = self.client.packages.download(package_id)
            except muranoclient_exc.HTTPException as e:
                msg = 'Error loading package id {0}: {1}'.format(
                    package_id, str(e)
                )
                exc_info = sys.exc_info()
                six.reraise(pkg_exc.PackageLoadError,
                            pkg_exc.PackageLoadError(msg),
                            exc_info[2])
            package_file = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as package_file:
                    package_file.write(package_data)

                with load_utils.load_from_file(
                        package_file.name,
                        target_dir=package_directory,
                        drop_dir=False) as app_package:
                    LOG.info(
                        "Successfully downloaded and unpacked "
                        "package {} {}".format(
                            package_def.fully_qualified_name, package_id))
                    self._downloaded.append(app_package)

                    self.try_cleanup_cache(
                        os.path.split(package_directory)[0],
                        current_id=package_id)
                    return app_package
            except IOError:
                msg = 'Unable to extract package data for %s' % package_id
                exc_info = sys.exc_info()
                six.reraise(pkg_exc.PackageLoadError,
                            pkg_exc.PackageLoadError(msg),
                            exc_info[2])
            finally:
                try:
                    if package_file:
                        os.remove(package_file.name)
                except OSError:
                    pass

    def try_cleanup_cache(self, package_directory=None, current_id=None):
        """Attempts to cleanup cache in a given directory.

        :param package_directory: directory containing cached packages
        :param current_id: optional id of the package to exclude from the list
        of deleted packages
        """
        if not package_directory:
            return

        try:
            pkg_ids_listed = set(os.listdir(package_directory))
        except OSError:
            # No directory for this package, probably someone
            # already deleted everything. Anyway nothing to delete
            return

        # if current_id was given: ensure it's not checked for removal
        pkg_ids_listed -= {current_id}

        for pkg_id in pkg_ids_listed:
            stale_directory = os.path.join(
                package_directory,
                pkg_id)

            if not os.path.isdir(package_directory):
                continue

            usage_lock_path = os.path.join(
                self._cache_directory,
                '{}_usage.lock'.format(pkg_id))
            ipc_lock = m_utils.ExclusiveInterProcessLock(
                path=usage_lock_path, sleep_func=eventlet.sleep)

            try:
                with usage_mem_locks[pkg_id].write_lock(False) as acquired:
                    if not acquired:
                        # the package is in use by other deployment in this
                        # process will do nothing, someone else would delete it
                        continue
                    acquired_ipc_lock = ipc_lock.acquire(blocking=False)
                    if not acquired_ipc_lock:
                        # the package is in use by other deployment in another
                        # process, will do nothing, someone else would delete
                        continue

                    shutil.rmtree(stale_directory,
                                  ignore_errors=True)
                    ipc_lock.release()

                    for lock_type in ('usage', 'download'):
                        lock_path = os.path.join(
                            self._cache_directory,
                            '{}_{}.lock'.format(pkg_id, lock_type))
                        try:
                            os.remove(lock_path)
                        except OSError:
                            LOG.warning("Couldn't delete lock file: "
                                        "{}".format(lock_path))
            except RuntimeError:
                # couldn't upgrade read lock to write-lock. go on.
                continue

    def _get_best_package_match(self, packages):
        public = None
        other = []
        for package in packages:
            if package.owner_id == self._execution_session.project_id:
                return package
            elif package.is_public:
                public = package
            else:
                other.append(package)
        if public is not None:
            return public
        elif other:
            return other[0]

    def _lock_usage(self, package_definition):
        """Locks package for usage"""

        # do not lock anything if we do not persist packages on disk
        if not CONF.engine.enable_packages_cache:
            return

        package_id = package_definition.id

        # A work around the fact that read_lock only supports `with` syntax.
        mem_lock = _with_to_generator(
            usage_mem_locks[package_id].read_lock())

        usage_lock_path = os.path.join(self._cache_directory,
                                       '{}_usage.lock'.format(package_id))
        ipc_lock = m_utils.SharedInterProcessLock(
            path=usage_lock_path,
            sleep_func=eventlet.sleep
        )
        ipc_lock = _with_to_generator(ipc_lock)

        next(mem_lock)
        next(ipc_lock)
        self._mem_locks.append(mem_lock)
        self._ipc_locks.append(ipc_lock)

    def import_fixation_table(self, fixations):
        self._fixations = deserialize_package_fixations(fixations)

    def export_fixation_table(self):
        return serialize_package_fixations(self._fixations)

    def compact_fixation_table(self):
        self._fixations = self._new_fixations.copy()

    def cleanup(self):
        """Cleans up any lock we had acquired and removes any stale packages"""

        if not CONF.engine.enable_packages_cache:
            shutil.rmtree(self._cache_directory, ignore_errors=True)
            return

        for lock in itertools.chain(self._mem_locks, self._ipc_locks):
            try:
                next(lock)
            except StopIteration:
                continue

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
        self._fixations = collections.defaultdict(set)
        self._new_fixations = collections.defaultdict(set)
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
                LOG.info('Unable to load package from path: {0}'.format(
                    folder))
                continue
            LOG.info('Loaded package from path {0}'.format(folder))

    def import_fixation_table(self, fixations):
        self._fixations = deserialize_package_fixations(fixations)

    def export_fixation_table(self):
        return serialize_package_fixations(self._fixations)

    def compact_fixation_table(self):
        self._fixations = self._new_fixations.copy()

    def load_class_package(self, class_name, version_spec):
        packages = self._packages_by_class.get(class_name)
        if not packages:
            raise exceptions.NoPackageForClassFound(class_name)
        version = version_spec.select(packages.keys())
        if not version:
            raise exceptions.NoPackageForClassFound(class_name)
        return packages[version]

    def load_package(self, package_name, version_spec):
        fixed_versions = self._fixations[package_name]
        version = version_spec.select(fixed_versions)
        if version:
            version_spec = helpers.parse_version_spec(version)
        packages = self._packages_by_name.get(package_name)
        if not packages:
            raise exceptions.NoPackageFound(package_name)
        version = version_spec.select(packages.keys())
        if not version:
            raise exceptions.NoPackageFound(package_name)
        self._fixations[package_name].add(version)
        self._new_fixations[package_name].add(version)
        return packages[version]

    def register_package(self, package):
        for c in package.classes:
            self._packages_by_class.setdefault(c, {})[
                package.version] = package
        self._packages_by_name.setdefault(package.name, {})[
            package.version] = package

    @property
    def packages(self):
        for package_versions in self._packages_by_name.values():
            for package in package_versions.values():
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

    def cleanup(self):
        """A stub for possible cleanup"""
        pass


class CombinedPackageLoader(package_loader.MuranoPackageLoader):
    def __init__(self, execution_session, root_loader=None):
        root_loader = root_loader or self
        self.api_loader = ApiPackageLoader(execution_session, root_loader)
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

    def export_fixation_table(self):
        result = deserialize_package_fixations(
            self.api_loader.export_fixation_table())
        for loader in self.directory_loaders:
            fixations = deserialize_package_fixations(
                loader.export_fixation_table())
            for key, value in fixations.items():
                result[key].update(value)
        return serialize_package_fixations(result)

    def import_fixation_table(self, fixations):
        self.api_loader.import_fixation_table(fixations)
        for loader in self.directory_loaders:
            loader.import_fixation_table(fixations)

    def compact_fixation_table(self):
        self.api_loader.compact_fixation_table()
        for loader in self.directory_loaders:
            loader.compact_fixation_table()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def cleanup(self):
        """Calls cleanup method of all loaders we combine"""
        self.api_loader.cleanup()
        for d_loader in self.directory_loaders:
            d_loader.cleanup()


def get_class(package, name):
    version = package.runtime_version
    loader = yaql_yaml_loader.get_loader(version)
    contents, file_id = package.get_class(name)
    return loader(contents, file_id)


def _with_to_generator(context_obj):
    with context_obj as obj:
        yield obj
    yield


def deserialize_package_fixations(fixations):
    result = collections.defaultdict(set)
    for name, versions in fixations.items():
        for version in versions:
            result[name].add(helpers.parse_version(version))
    return result


def serialize_package_fixations(fixations):
    return {
        name: list(str(v) for v in versions)
        for name, versions in fixations.items()
    }
