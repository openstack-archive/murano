# Copyright (c) 2015 Mirantis Inc.
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
import io
import os
import zipfile

import six

from murano.common.helpers import path


class PackageType(object):
    Library = 'Library'
    Application = 'Application'
    ALL = [Library, Application]


@six.add_metaclass(abc.ABCMeta)
class Package(object):
    def __init__(self, format_name, runtime_version, source_directory):
        self._source_directory = source_directory
        self._format_name = format_name
        self._runtime_version = runtime_version
        self._blob_cache = None

    @property
    def format_name(self):
        return self._format_name

    @abc.abstractproperty
    def full_name(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def version(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def classes(self):
        raise NotImplementedError()

    @property
    def runtime_version(self):
        return self._runtime_version

    @abc.abstractproperty
    def requirements(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def package_type(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def display_name(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def description(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def author(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def supplier(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def tags(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def logo(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def supplier_logo(self):
        raise NotImplementedError()

    @property
    def blob(self):
        if not self._blob_cache:
            self._blob_cache = _pack_dir(self._source_directory)
        return self._blob_cache

    @abc.abstractmethod
    def get_class(self, name):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_resource(self, name):
        raise NotImplementedError()

    @abc.abstractproperty
    def ui(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def meta(self):
        raise NotImplementedError()


def _zip_dir(base, zip_file):
    for root, _, files in os.walk(base):
        for f in files:
            abs_path = path.secure_join(root, f)
            relative_path = os.path.relpath(abs_path, base)
            zip_file.write(abs_path, relative_path)


def _pack_dir(source_directory):
    blob = io.BytesIO()
    zip_file = zipfile.ZipFile(blob, mode='w')
    _zip_dir(source_directory, zip_file)
    zip_file.close()

    return blob.getvalue()
