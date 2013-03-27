#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

import setuptools

from tabula.openstack.common import setup

requires = setup.parse_requirements()
depend_links = setup.parse_dependency_links()
project = 'tabula'

setuptools.setup(
    name=project,
    version=setup.get_version(project, '2013.1'),
    description="The OpenStack Dashboard.",
    license='Apache 2.0',
    author='OpenStack',
    author_email='horizon@lists.launchpad.net',
    url='https://github.com/openstack/horizon/',
    packages=setuptools.find_packages(exclude=['bin']),
    cmdclass=setup.get_cmdclass(),
    include_package_data=True,
    install_requires=requires,
    dependency_links=depend_links,
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Internet :: WWW/HTTP',
                 'Environment :: OpenStack']
)
