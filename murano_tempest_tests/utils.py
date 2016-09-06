# Copyright (c) 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import collections
import os
import shutil
import tempfile
import time
import uuid
import yaml
import zipfile

from oslo_log import log as logging
import requests
import six
from six.moves import urllib

LOG = logging.getLogger(__name__)

MANIFEST = {'Format': 'MuranoPL/1.0',
            'Type': 'Application',
            'Description': 'MockApp for API tests',
            'Author': 'Mirantis, Inc'}


def compose_package(app_name, package_dir,
                    require=None, archive_dir=None, add_class_name=False,
                    manifest_required=True, version=None):
    """Composes a murano package

    Composes package `app_name` manifest and files from `package_dir`.
    Includes `require` section if any in the manifest file.
    Puts the resulting .zip file into `archive_dir` if present or in the
    `package_dir`.
    """
    tmp_package_dir = os.path.join(archive_dir, os.path.basename(package_dir))
    shutil.copytree(package_dir, tmp_package_dir)
    package_dir = tmp_package_dir

    if manifest_required:
        manifest = os.path.join(package_dir, "manifest.yaml")
        with open(manifest, 'w') as f:
            fqn = 'io.murano.apps.' + app_name
            mfest_copy = MANIFEST.copy()
            mfest_copy['FullName'] = fqn
            mfest_copy['Name'] = app_name
            mfest_copy['Classes'] = {fqn: 'mock_muranopl.yaml'}
            if require:
                mfest_copy['Require'] = {str(name): version
                                         for name, version in require}
            if version:
                mfest_copy['Version'] = version
            f.write(yaml.dump(mfest_copy, default_flow_style=False))

    if add_class_name:
        class_file = os.path.join(package_dir, 'Classes', 'mock_muranopl.yaml')
        with open(class_file, 'r') as f:
            contents = f.read()

        index = contents.index('Extends')
        contents = "{0}Name: {1}\n\n{2}".format(contents[:index], app_name,
                                                contents[index:])
        with open(class_file, 'w') as f:
            f.write(contents)

    if require:
        class_file = os.path.join(package_dir, 'Classes', 'mock_muranopl.yaml')
        with open(class_file, 'r') as f:
            content = f.read()

        index_string = 'deploy:\n    Body:\n      '
        index = content.index(index_string) + len(index_string)
        class_names = [req[0][req[0].rfind('.') + 1:] for req in require]
        addition = "".join(["- new({})\n".format(name) + ' ' * 6
                            for name in class_names])
        content = content[:index] + addition + content[index:]
        with open(class_file, 'w') as f:
            f.write(content)

    name = app_name + '.zip'

    if not archive_dir:
        archive_dir = os.path.dirname(os.path.abspath(__file__))
    archive_path = os.path.join(archive_dir, name)

    with zipfile.ZipFile(archive_path, 'w') as zip_file:
        for root, dirs, files in os.walk(package_dir):
            for f in files:
                zip_file.write(
                    os.path.join(root, f),
                    arcname=os.path.join(os.path.relpath(root, package_dir), f)
                )

    return archive_path, name


def prepare_package(name, require=None, add_class_name=False,
                    app='MockApp', manifest_required=True,
                    version=None):
    """Prepare package.

    :param name: Package name to compose
    :param require: Parameter 'require' for manifest
    :param add_class_name: Option to write class name to class file
    :return: Path to archive, directory with archive, filename of archive
    """
    app_dir = acquire_package_directory(app=app)
    target_arc_path = tempfile.mkdtemp()

    arc_path, filename = compose_package(
        name, app_dir, require=require, archive_dir=target_arc_path,
        add_class_name=add_class_name, manifest_required=manifest_required,
        version=version)
    return arc_path, target_arc_path, filename


def generate_uuid():
    """Generate uuid for objects."""
    return uuid.uuid4().hex


def generate_name(prefix):
    """Generate name for objects."""
    suffix = generate_uuid()[:8]
    return '{0}_{1}'.format(prefix, suffix)


def acquire_package_directory(app='MockApp'):
    """Obtain absolutely directory with package files.

    Should be called inside tests dir.
    :return: Package path
    """
    top_plugin_dir = os.path.realpath(os.path.join(os.getcwd(),
                                                   os.path.dirname(__file__)))
    expected_package_dir = '/extras/' + app
    app_dir = top_plugin_dir + expected_package_dir
    return app_dir


def to_url(filename, base_url, version='', path='/', extension=''):
    if urllib.parse.urlparse(filename).scheme in ('http', 'https'):
        return filename
    if not base_url:
        raise ValueError("No base_url for repository supplied")
    if '/' in filename or filename in ('.', '..'):
        raise ValueError("Invalid filename path supplied: {0}".format(
            filename))
    version = '.' + version if version else ''
    return urllib.parse.urljoin(base_url,
                                path + filename + version + extension)

# ----------------------Murano client common functions-------------------------


class NoCloseProxy(object):
    """A proxy object, that does nothing on close."""
    def __init__(self, obj):
        self.obj = obj

    def close(self):
        return

    def __getattr__(self, name):
        return getattr(self.obj, name)


class File(object):
    def __init__(self, name, binary=True):
        self.name = name
        self.binary = binary

    def open(self):
        mode = 'rb' if self.binary else 'r'
        if hasattr(self.name, 'read'):
            # NOTE(kzaitsev) We do not want to close a file object
            # passed to File wrapper. The caller should be responsible
            # for closing it
            return NoCloseProxy(self.name)
        else:
            if os.path.isfile(self.name):
                return open(self.name, mode)
            url = urllib.parse.urlparse(self.name)
            if url.scheme in ('http', 'https'):
                resp = requests.get(self.name, stream=True)
                if not resp.ok:
                    raise ValueError("Got non-ok status({0}) "
                                     "while connecting to {1}".format(
                                         resp.status_code, self.name))
                temp_file = tempfile.NamedTemporaryFile(mode='w+b')
                for chunk in resp.iter_content(1024 * 1024):
                    temp_file.write(chunk)
                temp_file.flush()
                return open(temp_file.name, mode)
            raise ValueError("Can't open {0}".format(self.name))


class FileWrapperMixin(object):
    def __init__(self, file_wrapper):
        self.file_wrapper = file_wrapper
        try:
            self._file = self.file_wrapper.open()
        except Exception:
            # NOTE(kzaitsev): We need to have _file available at __del__ time.
            self._file = None
            raise

    def file(self):
        self._file.seek(0)
        return self._file

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()

    def save(self, dst, binary=True):
        file_name = self.file_wrapper.name

        if urllib.parse.urlparse(file_name).scheme:
            file_name = file_name.split('/')[-1]

        dst = os.path.join(dst, file_name)

        mode = 'wb' if binary else 'w'
        with open(dst, mode) as dst_file:
            self._file.seek(0)
            shutil.copyfileobj(self._file, dst_file)

    def __del__(self):
        self.close()


class Package(FileWrapperMixin):
    """Represents murano package contents."""

    @staticmethod
    def from_file(file_obj):
        if not isinstance(file_obj, File):
            file_obj = File(file_obj)
        return Package(file_obj)

    @staticmethod
    def from_location(name, base_url='', version='', url='', path=None):
        """Open file using one of three possible options

        If path is supplied search for name file in the path, otherwise
        if url is supplied - open that url and finally search murano
        repository for the package.
        """
        if path:
            pkg_name = os.path.join(path, name)
            file_name = None
            for f in [pkg_name, pkg_name + '.zip']:
                if os.path.exists(f):
                    file_name = f
            if file_name:
                return Package.from_file(file_name)
            LOG.error("Couldn't find file for package {0}, tried {1}".format(
                name, [pkg_name, pkg_name + '.zip']))
        if url:
            return Package.from_file(url)
        return Package.from_file(to_url(
            name,
            base_url=base_url,
            version=version,
            path='apps/',
            extension='.zip')
        )

    @property
    def contents(self):
        """Contents of a package."""
        if not hasattr(self, '_contents'):
            try:
                self._file.seek(0)
                self._zip_obj = zipfile.ZipFile(
                    six.BytesIO(self._file.read()))
            except Exception as e:
                LOG.error("Error {0} occurred,"
                          " while parsing the package".format(e))
                raise
        return self._zip_obj

    @property
    def manifest(self):
        """Parsed manifest file of a package."""
        if not hasattr(self, '_manifest'):
            try:
                self._manifest = yaml.safe_load(
                    self.contents.open('manifest.yaml'))
            except Exception as e:
                LOG.error("Error {0} occurred, while extracting "
                          "manifest from package".format(e))
                raise
        return self._manifest

    def images(self):
        """Returns a list of required image specifications."""
        if 'images.lst' not in self.contents.namelist():
            return []
        try:
            return yaml.safe_load(
                self.contents.open('images.lst')).get('Images', [])
        except Exception:
            return []

    @property
    def classes(self):
        if not hasattr(self, '_classes'):
            self._classes = {}
            for class_name, class_file in six.iteritems(
                    self.manifest.get('Classes', {})):
                filename = "Classes/%s" % class_file
                if filename not in self.contents.namelist():
                    continue
                klass = yaml.safe_load(self.contents.open(filename))
                self._classes[class_name] = klass
        return self._classes

    @property
    def ui(self):
        if not hasattr(self, '_ui'):
            if 'UI/ui.yaml' in self.contents.namelist():
                self._ui = self.contents.open('UI/ui.yaml')
            else:
                self._ui = None
        return self._ui

    @property
    def logo(self):
        if not hasattr(self, '_logo'):
            if 'logo.png' in self.contents.namelist():
                self._logo = self.contents.open('logo.png')
            else:
                self._logo = None
        return self._logo

    def _get_package_order(self, packages_graph):
        """Sorts packages according to dependencies between them

        Murano allows cyclic dependencies. It is impossible
        to do topological sort for graph with cycles, so at first
        graph condensation should be built.
        For condensation building Kosaraju's algorithm is used.
        Packages in strongly connected components can be situated
        in random order to each other.
        """
        def topological_sort(graph, start_node):
            order = []
            not_seen = set(graph)

            def dfs(node):
                not_seen.discard(node)
                for dep_node in graph[node]:
                    if dep_node in not_seen:
                        dfs(dep_node)
                order.append(node)

            dfs(start_node)
            return order

        def transpose_graph(graph):
            transposed = collections.defaultdict(list)
            for node, deps in six.viewitems(graph):
                for dep in deps:
                    transposed[dep].append(node)
            return transposed

        order = topological_sort(packages_graph, self.manifest['FullName'])
        order.reverse()
        transposed = transpose_graph(packages_graph)

        def top_sort_by_components(graph, component_order):
            result = []
            seen = set()

            def dfs(node):
                seen.add(node)
                result.append(node)
                for dep_node in graph[node]:
                    if dep_node not in seen:
                        dfs(dep_node)
            for item in component_order:
                if item not in seen:
                    dfs(item)
            return reversed(result)
        return top_sort_by_components(transposed, order)

    def requirements(self, base_url, path=None, dep_dict=None):
        """Scans Require section of manifests of all the dependencies.

        Returns a dict with FQPNs as keys and respective Package objects
        as values, ordered by topological sort.

        :param base_url: url of packages location
        :param path: local path of packages location
        :param dep_dict: unused. Left for backward compatibility
        """

        unordered_requirements = {}
        requirements_graph = collections.defaultdict(list)
        dep_queue = collections.deque([(self.manifest['FullName'], self)])
        while dep_queue:
            dep_name, dep_file = dep_queue.popleft()
            unordered_requirements[dep_name] = dep_file
            direct_deps = Package._get_direct_deps(dep_file, base_url, path)
            for name, file in direct_deps:
                if name not in unordered_requirements:
                    dep_queue.append((name, file))
            requirements_graph[dep_name] = [dep[0] for dep in direct_deps]

        ordered_reqs_names = self._get_package_order(requirements_graph)
        ordered_reqs_dict = collections.OrderedDict()
        for name in ordered_reqs_names:
            ordered_reqs_dict[name] = unordered_requirements[name]

        return ordered_reqs_dict

    @staticmethod
    def _get_direct_deps(package, base_url, path):
        result = []
        if 'Require' in package.manifest:
            for dep_name, ver in six.iteritems(package.manifest['Require']):
                try:
                    req_file = Package.from_location(
                        dep_name,
                        version=ver,
                        path=path,
                        base_url=base_url,
                    )
                except Exception as e:
                    LOG.error("Error {0} occurred while parsing package {1}, "
                              "required by {2} package".format(
                                  e, dep_name,
                                  package.manifest['FullName']))
                    continue
                result.append((req_file.manifest['FullName'], req_file))
        return result


class NamespaceResolver(object):
    """Copied from main murano repo

    original at murano/dsl/namespace_resolver.py
    """

    def __init__(self, namespaces):
        self._namespaces = namespaces
        self._namespaces[''] = ''

    def resolve_name(self, name, relative=None):
        if name is None:
            raise ValueError()
        if name and name.startswith(':'):
            return name[1:]
        if ':' in name:
            parts = name.split(':')
            if len(parts) != 2 or not parts[1]:
                raise NameError('Incorrectly formatted name ' + name)
            if parts[0] not in self._namespaces:
                raise KeyError('Unknown namespace prefix ' + parts[0])
            return '.'.join((self._namespaces[parts[0]], parts[1]))
        if not relative and '=' in self._namespaces and '.' not in name:
            return '.'.join((self._namespaces['='], name))
        if relative and '.' not in name:
            return '.'.join((relative, name))
        return name


def get_local_inheritance(classes):
    result = {}
    for class_name, klass in six.iteritems(classes):
        if 'Extends' not in klass:
            continue
        ns = klass.get('Namespaces')
        if ns:
            resolver = NamespaceResolver(ns)
        else:
            resolver = None

        if isinstance(klass['Extends'], list):
            bases = klass['Extends']
        else:
            bases = [klass['Extends']]
        for base_class in bases:
            if resolver:
                base_fqn = resolver.resolve_name(base_class)
            else:
                base_fqn = base_class
            result.setdefault(base_fqn, []).append(class_name)
    return result


def wait_for_environment_deploy(client, environment_id,
                                timeout=1800, interval=10):
    start_time = time.time()
    while client.get_environment(environment_id)['status'] == 'deploying':
        if time.time() - start_time > timeout:
            break
        time.sleep(interval)
    return client.get_environment(environment_id)
