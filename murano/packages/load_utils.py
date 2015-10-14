#    Copyright (c) 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import contextlib
import os
import shutil
import string
import sys
import tempfile
import zipfile

import semantic_version
import yaml

import murano.packages.exceptions as e
import murano.packages.hot_package
import murano.packages.mpl_package


@contextlib.contextmanager
def load_from_file(archive_path, target_dir=None, drop_dir=False):
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
            raise e.PackageFormatError("Uploaded file {0} is not a "
                                       "zip archive".format(archive_path))
        package = zipfile.ZipFile(archive_path)
        package.extractall(path=target_dir)
        yield load_from_dir(target_dir)
    except ValueError as err:
        raise e.PackageLoadError("Couldn't load package from file: "
                                 "{0}".format(err))
    finally:
        if drop_dir:
            if created:
                shutil.rmtree(target_dir)
            else:
                for f in os.listdir(target_dir):
                    os.unlink(os.path.join(target_dir, f))


def load_from_dir(source_directory, filename='manifest.yaml'):
    formats = {
        'MuranoPL': {
            ('1.0.0', '1.2.0'): murano.packages.mpl_package.MuranoPlPackage,
        },
        'Heat.HOT': {
            ('1.0.0', '1.0.0'): murano.packages.hot_package.HotPackage
        }
    }

    if not os.path.isdir(source_directory) or not os.path.exists(
            source_directory):
        raise e.PackageLoadError('Invalid package directory')
    full_path = os.path.join(source_directory, filename)
    if not os.path.isfile(full_path):
        raise e.PackageLoadError('Unable to find package manifest')

    try:
        with open(full_path) as stream:
            content = yaml.safe_load(stream)
    except Exception as ex:
        trace = sys.exc_info()[2]
        raise e.PackageLoadError(
            "Unable to load due to '{0}'".format(str(ex))), None, trace
    if content:
        p_format_spec = str(content.get('Format') or 'MuranoPL/1.0')
        if p_format_spec[0] in string.digits:
            p_format_spec = 'MuranoPL/' + p_format_spec
        parts = p_format_spec.split('/', 1)
        if parts[0] not in formats:
            raise e.PackageFormatError(
                'Unknown or missing format version')
        format_set = formats[parts[0]]
        version = semantic_version.Version('0.0.0')
        if len(parts) > 1:
            version = semantic_version.Version.coerce(parts[1])
        for key, value in format_set.iteritems():
            min_version = semantic_version.Version(key[0])
            max_version = semantic_version.Version(key[1])
            if min_version <= version <= max_version:
                return value(source_directory, content, parts[0], version)
        raise e.PackageFormatError(
            'Unsupported {0} format version {1}'.format(parts[0], version))
