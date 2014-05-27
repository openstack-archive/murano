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

import imghdr
import io
import os
import shutil
import sys
import tempfile
import yaml
import zipfile


import murano.packages.exceptions as e
import murano.packages.versions.v1


class DummyLoader(yaml.Loader):
    pass


def yaql_constructor(loader, node):
    value = loader.construct_scalar(node)
    return value

yaml.add_constructor(u'!yaql', yaql_constructor, DummyLoader)


class PackageTypes(object):
    Library = 'Library'
    Application = 'Application'
    ALL = [Library, Application]


class ApplicationPackage(object):
    def __init__(self, source_directory, manifest, loader=DummyLoader):
        self.yaml_loader = loader
        self._source_directory = source_directory
        self._full_name = None
        self._package_type = None
        self._display_name = None
        self._description = None
        self._author = None
        self._tags = None
        self._classes = None
        self._ui = None
        self._logo = None
        self._format = manifest.get('Format')
        self._ui_cache = None
        self._raw_ui_cache = None
        self._logo_cache = None
        self._classes_cache = {}
        self._blob_cache = None

    @property
    def full_name(self):
        return self._full_name

    @property
    def package_type(self):
        return self._package_type

    @property
    def display_name(self):
        return self._display_name

    @property
    def description(self):
        return self._description

    @property
    def author(self):
        return self._author

    @property
    def tags(self):
        return tuple(self._tags)

    @property
    def classes(self):
        return tuple(self._classes.keys())

    @property
    def ui(self):
        if not self._ui_cache:
            self._load_ui(True)
        return self._ui_cache

    @property
    def raw_ui(self):
        if not self._raw_ui_cache:
            self._load_ui(False)
        return self._raw_ui_cache

    @property
    def logo(self):
        if not self._logo_cache:
            self._load_logo(False)
        return self._logo_cache

    @property
    def blob(self):
        if not self._blob_cache:
            self._blob_cache = _pack_dir(self._source_directory)
        return self._blob_cache

    def get_class(self, name):
        if name not in self._classes_cache:
            self._load_class(name)
        return self._classes_cache[name]

    def get_resource(self, name):
        return os.path.join(self._source_directory, 'Resources', name)

    def validate(self):
        self._classes_cache.clear()
        for class_name in self._classes:
            self.get_class(class_name)
        self._load_ui(True)
        self._load_logo(True)

    # Private methods
    def _load_ui(self, load_yaml=False):
        if self._raw_ui_cache and load_yaml:
            self._ui_cache = yaml.load(self._raw_ui_cache, self.yaml_loader)
        else:
            ui_file = self._ui
            full_path = os.path.join(self._source_directory, 'UI', ui_file)
            if not os.path.isfile(full_path):
                self._raw_ui_cache = None
                self._ui_cache = None
                return
            try:
                with open(full_path) as stream:
                    self._raw_ui_cache = stream.read()
                    if load_yaml:
                        self._ui_cache = yaml.load(self._raw_ui_cache,
                                                   self.yaml_loader)
            except Exception as ex:
                trace = sys.exc_info()[2]
                raise e.PackageUILoadError(str(ex)), None, trace

    def _load_logo(self, validate=False):
        logo_file = self._logo or 'logo.png'
        full_path = os.path.join(self._source_directory, logo_file)
        if not os.path.isfile(full_path) and logo_file == 'logo.png':
            self._logo_cache = None
            return
        try:
            if validate:
                if imghdr.what(full_path) != 'png':
                    raise e.PackageLoadError("Logo is not in PNG format")
            with open(full_path) as stream:
                self._logo_cache = stream.read()
        except Exception as ex:
            trace = sys.exc_info()[2]
            raise e.PackageLoadError(
                "Unable to load logo: " + str(ex)), None, trace

    def _load_class(self, name):
        if name not in self._classes:
            raise e.PackageClassLoadError(name, 'Class not defined '
                                                'in this package')
        def_file = self._classes[name]
        full_path = os.path.join(self._source_directory, 'Classes', def_file)
        if not os.path.isfile(full_path):
            raise e.PackageClassLoadError(name, 'File with class '
                                                'definition not found')
        try:
            with open(full_path) as stream:
                self._classes_cache[name] = yaml.load(stream, self.yaml_loader)
        except Exception as ex:
            trace = sys.exc_info()[2]
            msg = 'Unable to load class definition due to "{0}"'.format(
                str(ex))
            raise e.PackageClassLoadError(name, msg), None, trace


def load_from_dir(source_directory, filename='manifest.yaml', preload=False,
                  loader=DummyLoader):
    formats = {'1.0': murano.packages.versions.v1}

    if not os.path.isdir(source_directory) or not os.path.exists(
            source_directory):
        raise e.PackageLoadError('Invalid package directory')
    full_path = os.path.join(source_directory, filename)
    if not os.path.isfile(full_path):
        raise e.PackageLoadError('Unable to find package manifest')

    try:
        with open(full_path) as stream:
            content = yaml.load(stream, DummyLoader)
    except Exception as ex:
        trace = sys.exc_info()[2]
        raise e.PackageLoadError(
            "Unable to load due to '{0}'".format(str(ex))), None, trace
    if content:
        p_format = str(content.get('Format'))
        if not p_format or p_format not in formats:
            raise e.PackageFormatError(
                'Unknown or missing format version')
        package = ApplicationPackage(source_directory, content, loader)
        formats[p_format].load(package, content)
        if preload:
            package.validate()
        return package


def _zipdir(path, zipf):
    for root, dirs, files in os.walk(path):
        for f in files:
            abspath = os.path.join(root, f)
            relpath = os.path.relpath(abspath, path)
            zipf.write(abspath, relpath)


def _pack_dir(source_directory):
    blob = io.BytesIO()
    zipf = zipfile.ZipFile(blob, mode='w')
    _zipdir(source_directory, zipf)
    zipf.close()

    return blob.getvalue()


def load_from_file(archive_path, target_dir=None, drop_dir=False,
                   loader=DummyLoader):
    if not os.path.isfile(archive_path):
        raise e.PackageLoadError('Unable to find package file')
    created = False
    if not target_dir:
        target_dir = tempfile.mkdtemp()
        created = True
    elif not os.path.exists(target_dir):
        os.mkdir(target_dir)
        created = True
    else:
        if os.listdir(target_dir):
            raise e.PackageLoadError('Target directory is not empty')

    try:
        if not zipfile.is_zipfile(archive_path):
            raise e.PackageFormatError("Uploading file should be a "
                                       "zip' archive")
        package = zipfile.ZipFile(archive_path)
        package.extractall(path=target_dir)
        return load_from_dir(target_dir, preload=True, loader=loader)
    finally:
        if drop_dir:
            if created:
                shutil.rmtree(target_dir)
            else:
                for f in os.listdir(target_dir):
                    os.unlink(os.path.join(target_dir, f))
