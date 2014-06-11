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

import re

import murano.packages.application_package
import murano.packages.exceptions as e
import murano.packages.mpl_package


# noinspection PyProtectedMember


def load(package, yaml_content):
    package._full_name = yaml_content.get('FullName')
    if not package._full_name:
        raise murano.packages.exceptions.PackageFormatError(
            'FullName not specified')
    _check_full_name(package._full_name)
    package._package_type = yaml_content.get('Type')
    if not package._package_type or package._package_type not in \
            murano.packages.application_package.PackageTypes.ALL:
        raise e.PackageFormatError('Invalid Package Type')
    package._display_name = yaml_content.get('Name', package._full_name)
    package._description = yaml_content.get('Description')
    package._author = yaml_content.get('Author')
    package._supplier = yaml_content.get('Supplier') or {}
    package._classes = yaml_content.get('Classes')
    package._ui = yaml_content.get('UI', 'ui.yaml')
    package._logo = yaml_content.get('Logo')
    package._tags = yaml_content.get('Tags')


def create(source_directory, content, loader):
    return murano.packages.mpl_package.MuranoPlPackage(
        source_directory, content, loader)


def _check_full_name(full_name):
    error = murano.packages.exceptions.PackageFormatError(
        'Invalid FullName')
    if re.match(r'^[\w\.]+$', full_name):
        if full_name.startswith('.') or full_name.endswith('.'):
            raise error
        if '..' in full_name:
            raise error
    else:
        raise error
