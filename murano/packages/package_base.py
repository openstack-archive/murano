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
import imghdr
import os
import re
import sys

import semantic_version

from murano.packages import exceptions
from murano.packages import package


class PackageBase(package.Package):
    def __init__(self, source_directory, manifest,
                 package_format, runtime_version):
        super(PackageBase, self).__init__(
            source_directory, package_format, runtime_version)
        self._full_name = manifest.get('FullName')
        if not self._full_name:
            raise exceptions.PackageFormatError('FullName is not specified')
        self._check_full_name(self._full_name)
        self._version = semantic_version.Version.coerce(str(manifest.get(
            'Version', '0.0.0')))
        self._package_type = manifest.get('Type')
        if self._package_type not in package.PackageType.ALL:
            raise exceptions.PackageFormatError(
                'Invalid package Type {0}'.format(self._package_type))
        self._display_name = manifest.get('Name', self._full_name)
        self._description = manifest.get('Description')
        self._author = manifest.get('Author')
        self._supplier = manifest.get('Supplier') or {}
        self._logo = manifest.get('Logo')
        self._tags = manifest.get('Tags')

        self._logo_cache = None
        self._supplier_logo_cache = None

    @abc.abstractproperty
    def requirements(self):
        raise NotImplementedError()

    @abc.abstractproperty
    def classes(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_class(self, name):
        raise NotImplementedError()

    @abc.abstractproperty
    def ui(self):
        raise NotImplementedError()

    @property
    def full_name(self):
        return self._full_name

    @property
    def version(self):
        return self._version

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
    def supplier(self):
        return self._supplier

    @property
    def tags(self):
        return list(self._tags)

    @property
    def logo(self):
        return self._load_image(self._logo, 'logo.png', 'logo')

    @property
    def supplier_logo(self):
        return self._load_image(
            self._supplier.get('Logo'), 'supplier_logo.png', 'supplier logo')

    def get_resource(self, name):
        resources_dir = os.path.join(self._source_directory, 'Resources')
        if not os.path.exists(resources_dir):
            os.makedirs(resources_dir)
        return os.path.join(resources_dir, name)

    def _load_image(self, file_name, default_name, what_image):
        full_path = os.path.join(
            self._source_directory, file_name or default_name)
        if not os.path.isfile(full_path) and not file_name:
            return
        try:
            if imghdr.what(full_path) != 'png':
                raise exceptions.PackageLoadError(
                    '{0} is not in PNG format'.format(what_image))
            with open(full_path) as stream:
                return stream.read()
        except Exception as ex:
            trace = sys.exc_info()[2]
            raise exceptions.PackageLoadError(
                'Unable to load {0}: {1}'.format(what_image, ex)), None, trace

    @staticmethod
    def _check_full_name(full_name):
        error = exceptions.PackageFormatError('Invalid FullName ' + full_name)
        if re.match(r'^[\w\.]+$', full_name):
            if full_name.startswith('.') or full_name.endswith('.'):
                raise error
            if '..' in full_name:
                raise error
        else:
            raise error
