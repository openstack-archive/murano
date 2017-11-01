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
import sys
import tempfile
import zipfile

import six
import yaml

from murano.common.helpers import path
from murano.common.plugins import package_types_loader
import murano.packages.exceptions as e
import murano.packages.hot_package
import murano.packages.mpl_package


PLUGIN_LOADER = None


def get_plugin_loader():
    global PLUGIN_LOADER

    if PLUGIN_LOADER is None:
        PLUGIN_LOADER = package_types_loader.PluginLoader()
        for runtime_version in ('1.0', '1.1', '1.2', '1.3', '1.4'):
            format_string = 'MuranoPL/' + runtime_version
            PLUGIN_LOADER.register_format(
                format_string, murano.packages.mpl_package.MuranoPlPackage)
        PLUGIN_LOADER.register_format(
            'Heat.HOT/1.0', murano.packages.hot_package.HotPackage)
    return PLUGIN_LOADER


@contextlib.contextmanager
def load_from_file(archive_path, target_dir=None, drop_dir=False):
    if not os.path.isfile(archive_path):
        raise e.PackageLoadError('Unable to find package file')
    created = False
    if not target_dir:
        target_dir = tempfile.mkdtemp()
        created = True
    elif not os.path.exists(target_dir):
        os.makedirs(target_dir)
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
                    os.unlink(path.secure_join(target_dir, f))


def load_from_dir(source_directory, filename='manifest.yaml'):
    if not os.path.isdir(source_directory) or not os.path.exists(
            source_directory):
        raise e.PackageLoadError('Invalid package directory')
    full_path = path.secure_join(source_directory, filename)
    if not os.path.isfile(full_path):
        raise e.PackageLoadError('Unable to find package manifest')

    try:
        with open(full_path) as stream:
            content = yaml.safe_load(stream)
    except Exception as ex:
        trace = sys.exc_info()[2]
        six.reraise(
            e.PackageLoadError,
            e.PackageLoadError("Unable to load due to '{0}'".format(ex)),
            trace)
    else:
        format_spec = str(content.get('Format') or 'MuranoPL/1.0')
        if format_spec[0].isdigit():
            format_spec = 'MuranoPL/' + format_spec
        plugin_loader = get_plugin_loader()
        handler = plugin_loader.get_package_handler(format_spec)
        if handler is None:
            raise e.PackageFormatError(
                'Unsupported format {0}'.format(format_spec))
        return handler(source_directory, content)
