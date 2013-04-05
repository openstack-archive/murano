#    Copyright (c) 2013 Mirantis, Inc.
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

from glazierclient.openstack.common import setup

project = 'python-glazierclient'


setuptools.setup(
    name=project,
    version=setup.get_version(project, '2013.1'),
    author='Mirantis, Inc.',
    author_email='smelikyan@mirantis.com',
    description="Client library for Glazier Project",
    license='Apache',
    url='http://glazier.mirantis.com/',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    install_requires=setup.parse_requirements(),
    test_suite="nose.collector",
    cmdclass=setup.get_cmdclass(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': ['glazier = glazierclient.shell:main']
    },
    dependency_links=setup.parse_dependency_links(),
    tests_require=setup.parse_requirements(['tools/test-requires']),
    setup_requires=['setuptools-git>=0.4'],
)
