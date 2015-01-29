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

import os
import shutil
import sys
import tempfile
import zipfile

import yaml

from murano.engine import yaql_yaml_loader
import murano.packages.application_package
import murano.packages.exceptions as e
import murano.packages.versions.hot_v1
import murano.packages.versions.mpl_v1


def load_from_file(archive_path, target_dir=None, drop_dir=False,
                   loader=yaql_yaml_loader.YaqlYamlLoader):
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
        return load_from_dir(target_dir, preload=True, loader=loader)
    finally:
        if drop_dir:
            if created:
                shutil.rmtree(target_dir)
            else:
                for f in os.listdir(target_dir):
                    os.unlink(os.path.join(target_dir, f))


def load_from_dir(source_directory, filename='manifest.yaml', preload=False,
                  loader=yaql_yaml_loader.YaqlYamlLoader):
    formats = {
        '1.0': murano.packages.versions.mpl_v1,
        'MuranoPL/1.0': murano.packages.versions.mpl_v1,
        'Heat.HOT/1.0': murano.packages.versions.hot_v1
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
        p_format = str(content.get('Format'))
        if not p_format or p_format not in formats:
            raise e.PackageFormatError(
                'Unknown or missing format version')
        package = formats[p_format].create(source_directory, content, loader)
        formats[p_format].load(package, content)
        if preload:
            package.validate()
        return package
