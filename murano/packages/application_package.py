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
import sys
import zipfile

import murano.packages.exceptions as e


class PackageTypes(object):
    Library = 'Library'
    Application = 'Application'
    ALL = [Library, Application]


class ApplicationPackage(object):
    def __init__(self, source_directory, manifest, loader):
        self.yaml_loader = loader
        self._source_directory = source_directory
        self._full_name = None
        self._package_type = None
        self._display_name = None
        self._description = None
        self._author = None
        self._supplier = {}
        self._tags = None
        self._logo = None
        self._format = manifest.get('Format')
        self._logo_cache = None
        self._supplier_logo_cache = None
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
    def supplier(self):
        return self._supplier

    @property
    def tags(self):
        return list(self._tags)

    @property
    def logo(self):
        if not self._logo_cache:
            self._load_logo(False)
        return self._logo_cache

    @property
    def supplier_logo(self):
        if not self._supplier_logo_cache:
            self._load_supplier_logo(False)
        return self._supplier_logo_cache

    @property
    def blob(self):
        if not self._blob_cache:
            self._blob_cache = _pack_dir(self._source_directory)
        return self._blob_cache

    def get_resource(self, name):
        resources_dir = os.path.join(self._source_directory, 'Resources')
        if not os.path.exists(resources_dir):
            os.makedirs(resources_dir)
        return os.path.join(resources_dir, name)

    def validate(self):
        self._load_logo(True)
        self._load_supplier_logo(True)

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

    def _load_supplier_logo(self, validate=False):
        if 'Logo' not in self._supplier:
            self._supplier['Logo'] = None
        logo_file = self._supplier['Logo'] or 'supplier_logo.png'
        full_path = os.path.join(self._source_directory, logo_file)
        if not os.path.isfile(full_path) and logo_file == 'supplier_logo.png':
            del self._supplier['Logo']
            return
        try:
            if validate:
                if imghdr.what(full_path) != 'png':
                    raise e.PackageLoadError(
                        "Supplier Logo is not in PNG format")
            with open(full_path) as stream:
                self._supplier_logo_cache = stream.read()
        except Exception as ex:
            trace = sys.exc_info()[2]
            raise e.PackageLoadError(
                "Unable to load supplier logo: " + str(ex)), None, trace


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
