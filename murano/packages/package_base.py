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
import six

from murano.common.helpers import path
from murano.common.i18n import _
from murano.packages import exceptions
from murano.packages import package


class PackageBase(package.Package):
    def __init__(self, format_name, runtime_version,
                 source_directory, manifest):
        super(PackageBase, self).__init__(
            format_name, runtime_version, source_directory)
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
        self._tags = manifest.get('Tags', [])

        self._logo_cache = None
        self._supplier_logo_cache = None
        self._source_directory = source_directory

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
    def source_directory(self):
        return self._source_directory

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
    def meta(self):
        return None

    @property
    def supplier_logo(self):
        return self._load_image(
            self._supplier.get('Logo'), 'supplier_logo.png', 'supplier logo')

    def get_resource(self, name):
        resources_dir = path.secure_join(self._source_directory, 'Resources')
        if not os.path.exists(resources_dir):
            os.makedirs(resources_dir)
        return path.secure_join(resources_dir, name)

    def _load_image(self, file_name, default_name, what_image):
        full_path = path.secure_join(
            self._source_directory, file_name or default_name)
        if not os.path.isfile(full_path) and not file_name:
            return

        allowed_ftype = ('png', 'jpeg', 'gif')
        allowed_size = 500 * 1024
        try:

            if imghdr.what(full_path) not in allowed_ftype:
                msg = _('{0}: Unsupported Format. Only {1} allowed').format(
                    what_image, ', '.join(allowed_ftype))

                raise exceptions.PackageLoadError(msg)

            fsize = os.stat(full_path).st_size
            if fsize > allowed_size:
                msg = _('{0}: Uploaded image size {1} is too large. '
                        'Max allowed size is {2}').format(
                    what_image, fsize, allowed_size)
                raise exceptions.PackageLoadError(msg)

            with open(full_path, 'rb') as stream:
                return stream.read()

        except Exception as ex:
            trace = sys.exc_info()[2]
            six.reraise(exceptions.PackageLoadError,
                        exceptions.PackageLoadError(
                            'Unable to load {0}: {1}'.format(what_image, ex)),
                        trace)

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
