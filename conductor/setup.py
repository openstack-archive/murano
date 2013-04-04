#!/usr/bin/python
# Copyright (c) 2010 OpenStack, LLC.
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

import setuptools

from conductor.openstack.common import setup

requires = setup.parse_requirements()
depend_links = setup.parse_dependency_links()
project = 'conductor'

setuptools.setup(
    name=project,
    version=setup.get_version(project, '2013.1'),
    description='The Conductor is orchestration engine server',
    license='Apache License (2.0)',
    author='Mirantis, Inc.',
    author_email='openstack@lists.launchpad.net',
    url='http://conductor.openstack.org/',
    packages=setuptools.find_packages(exclude=['bin']),
    test_suite='nose.collector',
    cmdclass=setup.get_cmdclass(),
    include_package_data=True,
    install_requires=requires,
    dependency_links=depend_links,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
        'Environment :: OpenStack',
    ],
    scripts=['bin/conductor'],
    py_modules=[]
)
