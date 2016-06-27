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

import os
import uuid
import yaml
import zipfile


MANIFEST = {'Format': 'MuranoPL/1.0',
            'Type': 'Application',
            'Description': 'MockApp for API tests',
            'Author': 'Mirantis, Inc'}


def compose_package(app_name, manifest, package_dir,
                    require=None, archive_dir=None, add_class_name=False):
    """Composes a murano package

    Composes package `app_name` with `manifest` file as a template for the
    manifest and files from `package_dir`.
    Includes `require` section if any in the manifest file.
    Puts the resulting .zip file into `acrhive_dir` if present or in the
    `package_dir`.
    """
    with open(manifest, 'w') as f:
        fqn = 'io.murano.apps.' + app_name
        mfest_copy = MANIFEST.copy()
        mfest_copy['FullName'] = fqn
        mfest_copy['Name'] = app_name
        mfest_copy['Classes'] = {fqn: 'mock_muranopl.yaml'}
        if require:
            mfest_copy['Require'] = require
        f.write(yaml.dump(mfest_copy, default_flow_style=False))

    if add_class_name:
        class_file = os.path.join(package_dir, 'Classes', 'mock_muranopl.yaml')
        with open(class_file, 'r+') as f:
            line = ''
            while line != '# Write name into next line\n':
                line = f.readline()
            f.write('Name: {0}'.format(app_name))

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


def prepare_package(name, require=None, add_class_name=False):
    """Prepare package.

    :param name: Package name to compose
    :param require: Parameter 'require' for manifest
    :param add_class_name: Option to write class name to class file
    :return: Path to archive, directory with archive, filename of archive
    """
    app_dir = acquire_package_directory()
    target_arc_path = app_dir.rsplit('MockApp', 1)[0]

    arc_path, filename = compose_package(
        name, os.path.join(app_dir, 'manifest.yaml'),
        app_dir, require=require, archive_dir=target_arc_path,
        add_class_name=add_class_name)
    return arc_path, target_arc_path, filename


def generate_uuid():
    """Generate uuid for objects."""
    return uuid.uuid4().hex


def generate_name(prefix):
    """Generate name for objects."""
    suffix = generate_uuid()[:8]
    return '{0}_{1}'.format(prefix, suffix)


def acquire_package_directory():
    """Obtain absolutely directory with package files.

    Should be called inside tests dir.
    :return: Package path
    """
    top_plugin_dir = os.path.realpath(os.path.join(os.getcwd(),
                                                   os.path.dirname(__file__)))
    expected_package_dir = '/extras/MockApp'
    app_dir = top_plugin_dir + expected_package_dir
    return app_dir
