..
      Copyright 2014 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http//www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

==================================
Murano Automated Tests Description
==================================
This page describes automated tests for OpenStack Murano project: how you can download and run tests, how understand the root of problems with FAILed tests and detailed description about each test, which executes upon every commit.

Murano Continious Integration Service
=====================================
Murano project has the CI server, which tests all commits for Murano components and verifies that new code does not break nothing.

Murano CI uses OpenStack QA cloud for testing infrastructure.

Murano CI url: https://murano-ci.mirantis.com/jenkins/

There are two jobs for the **murano** repository and two jobs for the **murano-dashboard** repository : one of them runs on Ubuntu, another one on CentOS.

Here you can see several Jenkins jobs with different targets:

* Jobs "murano-dashboard-integration-tests-\*" allow to verify each commit to murano-dashboard repository on different distributive
* Jobs "murano-engine-app-deployment-tests-\*" allow to verify each commit to murano repository on different distributive

Other jobs allow to build and test Murano documentation and perform another usefull work to support Murano CI infrastructure.


Murano Automated Tests: UI Tests
================================

Murano project has a Web User Interface and we have the test suite for Murano Web UI. All UI tests are located at the https://github.com/stackforge/murano-dashboard/functionaltests

All automated tests for Murano Web UI are written on Python using advanced Selenium library.This library allows to find Web elements using captions for fields and other information to find elements without/with xpath. For more information please visit http://selenium-python.readthedocs.org/

How To Run
----------

Prerequisites:
++++++++++++++

* Install Python module called nose using **easy_install nose** or **pip install nose**
  This will install the nose libraries, as well as the nosetests script, which you can use to automatically discover and run tests.
* Install external Python libraries which are required for Murano Web UI tests: **testtools** and **selenium**

Download tests and run:
+++++++++++++++++++++++

First of all make sure that all additional components are installed.

* Clone murano-dashboard git repository:

    *git clone https://github.com/stackforge/murano-dashboard*
* Change default settings:
    * Open functionaltests/config/config_file.conf
    * Set appropriate urls and credentials.

::

    [common]
    horizon_url = http://localhost/horizon
    murano_url = http://localhost:8082
    user = ***
    password = ***
    tenant = ***
    keystone_url = http://localhost:5000/v2.0/

* Go to the "functionaltests" directory where tests are stored
* Some applications need to be uploaded to the Application Catalog since some tests use them. To upload a set of standard packages from special Murano repository need to create and execute following script which clone repository with packages, archive and store them in 'functionaltests' folder:

::

    git_url="https://github.com/murano-project/murano-app-incubator"
    clone_dir="murano-app-incubator"
    git clone $git_url $clone_dir
    cd $clone_dir
    for package_dir in io.murano.*
    do
        if [ -d "$package_dir" ]; then
            if [ -f "${package_dir}/manifest.yaml" ]; then
                sudo bash make-package.sh $package_dir
            fi
        fi
    done

* All preparation is done.
* All tests are grouped for a few suites. To specify which tests/suite to run, pass test/suite names on the command line:

    * to run all tests: *nosetests sanity_check.py*
    * to run single suite: *nosetests sanity_check.py:<test suite name>*
    * to run single test: *nosetests sanity_check.py:<test suite name>.<test name>*

In case of SUCCESS you should see something like this:

.........................

Ran 34 tests in 1.440s

OK

There are also a number of command line options that can be used to control the test execution and generated outputs. For help with nosetests’ many command-line options, try:

*nosetests -h*


Murano Automated Tests: Tempest Tests
=====================================

All Murano services have tempest-based automated tests, which allow to verify API interfaces and deployment scenarious.

Tempest tests for Murano are located at the: https://github.com/stackforge/murano/tree/master/functionaltests

The following Python files are contain basic tests suites for different Murano components.
Tests on API which running on devstack gate can be founded here https://github.com/stackforge/murano/tree/master/functionaltests/api

* test_murano_envs.py contains test suite with actions on murano's environments(create, delete, get and etc.)
* test_murano_sessions.py contains test suite with actions on murano's sessions(create, delete, get and etc.)
* test_murano_services.py contains test suite with actions on murano's services(create, delete, get and etc.)
* test_murano_repository.py contains test suite with actions on murano's package repository

Tests on engine which running on murano-ci : https://github.com/stackforge/murano/tree/master/functionaltests/engine

* base.py contains base test class and tests with actions on deploy murano's services

If you want to know, what steps this test performs, you can see test's scenario in code. For example:

::

    @attr(type='smoke')
    def test_get_environment(self):
        """
        Get environment by id
        Test create environment, afterthat test try to get
        environment's info, using environment's id,
        and finally delete this environment
        Target component: Murano
        Scenario:
            1. Send request to create environment.
            2. Send request to get environment
            3. Send request to delete environment
        """
        resp, env = self.create_environment('test')
        self.environments.append(env)
        resp, infa = self.get_environment_by_id(env['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual('test', infa['name'])
        self.delete_environment(env['id'])
        self.environments.pop(self.environments.index(env))
