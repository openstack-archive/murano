.. _test_docs:

==================================
Murano automated tests description
==================================

This page describes automated tests for a Murano project:

* where tests are located
* how they are run
* how to execute tests on a local machine
* how to find the root of problems with FAILed tests

Murano continuous integration service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Murano project has separate CI server, which runs tests for all commits and
verifies that new code does not break anything.

Murano CI uses OpenStack QA cloud for testing infrastructure.

Murano CI url: https://murano-ci.mirantis.com/jenkins/ Anyone can login
to that server, using launchpad credentials.

There you can find each job for each repository: one for **murano** and
another one for **murano-dashboard**.

* ``gate-murano-dashboard-ubuntu\*`` verifies each commit to
  the murano-dashboard repository
* ``gate-murano-ubuntu\*`` verifies each commit to the murano repository

Other jobs allow one to build and test Murano documentation and to perform other
useful work to support the Murano CI infrastructure.
All jobs are run following a fresh installation of the operating system and all components
are installed on each run.

UI tests
~~~~~~~~

The Murano project has a web user interface and all possible user scenarios
should be tested.
All UI tests are located at
``https://git.openstack.org/cgit/openstack/murano-dashboard/tree/muranodashboard/tests/functional``.

Automated tests for the Murano web UI are written in Python using the special
Selenium library. This library is used to automate web browser interactions
with Python. See official `Selenium documentation <https://selenium-python.readthedocs.org/>`_
for details.

Prerequisites:
--------------

* Install the Python module called nose using either the
  :command:`easy_install nose` or :command:`pip install nose` command.
  This will install the nose libraries, as well as the ``nosetests`` script,
  which you can use to automatically discover and run tests.
* Install external Python libraries, which are required for the Murano web UI
  tests: ``testtools`` and ``selenium``.
* Verify that you have one of the following web browsers installed:

  * Mozilla Firefox 46.0

    .. note::

       If you do not have Firefox package out of the box,
       install and remove it. Otherwise, you will need to install
       dependent libraries manually. To downgrade Firefox:

       .. code-block:: console

          apt-get remove firefox
          wget https://ftp.mozilla.org/pub/firefox/releases/46.0/linux-x86_64/en-US/firefox-46.0.tar.bz2
          tar -xjf firefox-46.0.tar.bz2
          rm -rf /opt/firefox
          mv firefox /opt/firefox46
          ln -s /opt/firefox46/firefox /usr/bin/firefox

  * Google Chrome

* To run the tests on a remote server, configure the remote X server.
  Use VNC Software to see the test results in real-time.

  #. Specify the display environment variable:

     .. code-block:: console

        $DISPLAY=: <value>

  #. Configure remote X server and VNC Software by typing:

     .. code-block:: console

        apt-get install xvfb xfonts-100dpi xfonts-75dpi xfonts-cyrillic xorg dbus-x11
        "Xvfb -fp "/usr/share/fonts/X11/misc/" :$DISPLAY -screen 0 "1280x1024x16" &"
        apt-get install --yes x11vnc
        x11vnc -bg -forever -nopw -display :$DISPLAY -ncache 10
        sudo iptables -I INPUT 1 -p tcp --dport 5900 -j ACCEPT

Download and run tests
----------------------

To download and run the tests:

#. Verify that all additional components has been installed.

#. Clone the ``murano-dashboard`` git repository:

   .. code-block:: console

      git clone https://git.openstack.org/openstack/murano-dashboard

#. Change the default settings:

   #. Specify the Murano Repository URL variable for Horizon local settings
      in ``murano_dashboard/muranodashboard/local/local_settings.d/_50_murano.py``:

      .. code-block:: console

         MURANO_REPO_URL = 'http://localhost:8099'

   #. Copy ``muranodashboard/tests/functional/config/config.conf.sample`` to
      ``config.conf``.

   #. Set appropriate URLs and credentials for your OpenStack lab.
      Only Administrator user credentials are appropriate.

      .. code-block:: console

        [murano]

        horizon_url = http://localhost/dashboard
        murano_url = http://localhost:8082
        user = ***
        password = ***
        tenant = ***
        keystone_url = http://localhost:5000/v3

All tests are kept in ``sanity_check.py`` and divided into 10 test suites:

* TestSuiteSmoke - verification of Murano panels; checks that they can be open
  without errors.
* TestSuiteEnvironment - verification of all operations with environment are
  finished successfully.
* TestSuiteImage - verification of operations with images.
* TestSuiteFields - verification of custom fields validators.
* TestSuitePackages - verification of operations with Murano packages.
* TestSuiteApplications - verification of Application Catalog page and of
  application creation process.
* TestSuiteAppsPagination - verification of apps pagination in case of many
  applications installed.
* TestSuiteRepository - verification of importing packages and bundles.
* TestSuitePackageCategory - verification of main operations with categories.
* TestSuiteCategoriesPagination - verification of categories pagination
  in case of many categories created.
* TestSuiteMultipleEnvironments - verification of ability to apply action
  to multiple environments.

To run the tests follow these instructions:

* To run all tests:

.. code-block:: console

   nosetests sanity_check.py

* To run a single suite:

.. code-block:: console

   nosetests sanity_check.py:<test suite name>

* To run a single test:

.. code-block:: console

   nosetests sanity_check.py:<test suite name>.<test name>


In case of successful execution, you should see something like this:

.. code-block:: console

   .........................
   Ran 34 tests in 1.440s
   OK

In case of failure, the folder with screenshots of the last operation of
tests that finished with errors would be created.
It is located in ``muranodashboard/tests/functional`` folder.

There are also a number of command line options that can be used to control
the test execution and generated outputs. For more details about ``nosetests``,
type:

.. code-block:: console

   nosetests -h


Tempest tests
~~~~~~~~~~~~~

All Murano services have tempest-based automated tests, which verify
API interfaces and deployment scenarios.
Tempest tests for Murano are located at ``https://git.openstack.org/cgit/openstack/murano/tree/murano/tests/functional``.

The following Python files contain basic test suites for different Murano components.

API tests
---------

Murano API tests are run on the devstack gate located at
``https://git.openstack.org/cgit/openstack/murano/tree/murano/tests/functional/api``.

* ``test_murano_envs.py`` contains test suite with actions on murano
  environments (create, delete, get, and others).
* ``test_murano_sessions.py`` contains test suite with actions on murano
  sessions (create, delete, get, and others).
* ``test_murano_services.py`` contains test suite with actions on murano
  services (create, delete, get, and others).
* ``test_murano_repository.py`` contains test suite with actions on murano
  package repository.

Engine tests
------------

Murano Engine Tests are run on murano-ci at ``https://git.openstack.org/cgit/openstack/murano/tree/murano/tests/functional/engine``:

* ``base.py`` contains base test class and tests with actions on deploy
  Murano services such as Telnet and Apache.

Command-line interface tests
----------------------------

Murano CLI tests are currently in the middle of creation. The current scope
is read-only operations on a cloud that are hard to test through unit tests.
All tests have description and execution steps in their docstrings.
