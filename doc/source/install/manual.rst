..
    Copyright 2014 Mirantis, Inc.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.
..

.. _installing_manually:

===============================
Installing and Running Manually
===============================

Prepare Environment
===================

Install Prerequisites
---------------------

First you need to install a number of packages with your OS package manager.
The list of packages depends on the OS you use.

Ubuntu
^^^^^^

.. code-block:: console

    $ sudo apt-get install python-pip python-dev \
    > libmysqlclient-dev libpq-dev \
    > libxml2-dev libxslt1-dev \
    > libffi-dev
..

Fedora
^^^^^^

.. note::

    Fedora support wasn't thoroughly tested. We do not guarantee that Murano
    will work on Fedora.
..

.. code-block:: console

    $ sudo yum install gcc python-setuptools python-devel python-pip
..


CentOS
^^^^^^

.. code-block:: console

    $ sudo yum install gcc python-setuptools python-devel
    $ sudo easy_install pip
..


Install tox
-----------

.. code-block:: console

    $ sudo pip install tox
..


Install And Configure Database
------------------------------

Murano can use various database types on backend. For development purposes
SQLite is enough in most cases. For production installations you should use
MySQL or PostgreSQL databases.

.. warning::

    Although Murano could use PostgreSQL database on backend, it wasn't
    thoroughly tested and should be used with caution.
..

To use MySQL database you should install it and create an empty database first:

.. code-block:: console

    $ apt-get install python-mysqldb mysql-server
..

.. code-block:: console

    $ mysql -u root -p
    mysql> CREATE DATABASE murano;
    mysql> GRANT ALL PRIVILEGES ON murano.* TO 'murano'@'localhost' \
        IDENTIFIED BY 'MURANO_DBPASS';
    mysql> exit;
..


Install the API service and Engine
==================================

1.  Create a folder which will hold all Murano components.

    .. code-block:: console

        $ mkdir ~/murano
    ..

2.  Clone the Murano git repository to the management server.

    .. code-block:: console

        $ cd ~/murano
        $ git clone https://github.com/stackforge/murano
    ..

3.  Copy the sample configuration from the source tree to their final location.

    .. code-block:: console

        $ cd ~/murano/murano/etc/murano
        $ cp murano.conf.sample murano.conf
    ..

4.  Edit ``murano.conf`` with your favorite editor. Below is an example
    which contains basic settings your are likely need to configure.

    .. note::

        The example below uses SQLite database. Edit **[database]** section
        if you want to use other database type.
    ..

    .. code-block:: ini

        [DEFAULT]
        debug = true
        verbose = true
        rabbit_host = %RABBITMQ_SERVER_IP%
        rabbit_userid = %RABBITMQ_USER%
        rabbit_password = %RABBITMQ_PASSWORD%
        rabbit_virtual_host = %RABBITMQ_SERVER_VIRTUAL_HOST%
        notification_driver = messagingv2

        [database]
        backend = sqlalchemy
        connection = sqlite:///murano.sqlite

        [keystone]
        auth_url = 'http://%OPENSTACK_HOST_IP%:5000/v2.0'

        [keystone_authtoken]
        auth_uri = 'http://%OPENSTACK_HOST_IP%:5000/v2.0'
        auth_host = '%OPENSTACK_HOST_IP%'
        auth_port = 5000
        auth_protocol = http
        admin_tenant_name = %OPENSTACK_ADMIN_TENANT%
        admin_user = %OPENSTACK_ADMIN_USER%
        admin_password = %OPENSTACK_ADMIN_PASSWORD%

        [murano]
        url = http://%YOUR_HOST_IP%:8082

        [rabbitmq]
        host = %RABBITMQ_SERVER_IP%
        login = %RABBITMQ_USER%
        password = %RABBITMQ_PASSWORD%
        virtual_host = %RABBITMQ_SERVER_VIRTUAL_HOST%
    ..

5.  Create a virtual environment and install Murano prerequisites. We will use
    *tox* for that. Virtual environment will be created under *.tox* directory.

    .. code-block:: console

        $ cd ~/murano/murano
        $ tox
    ..

6.  Create database tables for Murano.

    .. code-block:: console

        $ cd ~/murano/murano
        $ tox -e venv -- murano-db-manage \
        > --config-file ./etc/murano/murano.conf upgrade
    ..

7.  Open a new console and launch Murano API. A separate terminal is
    required because the console will be locked by a running process.

    .. code-block:: console

        $ cd ~/murano/murano
        $ tox -e venv -- murano-api \
        > --config-file ./etc/murano/murano.conf
    ..

8.  Import Core Murano Library.

    .. code-block:: console

        $ cd ~/murano/murano
        $ tox -e venv -- murano-manage \
        > --config-file ./etc/murano/murano.conf \
        > import-package ./meta/io.murano
    ..

8.  Open a new console and launch Murano Engine. A separate terminal is
    required because the console will be locked by a running process.

    .. code-block:: console

        $ cd ~/murano/murano
        $ tox -e venv -- murano-engine --config-file ./etc/murano/murano.conf
    ..


Install Murano Dashboard
========================

 Murano API & Engine services provide the core of Murano. However, your need a
 control plane to use it. This section decribes how to install and run Murano
 Dashboard.

1.  Clone the repository with Murano Dashboard.

    .. code-block:: console

        $ cd ~/murano
        $ git clone https://github.com/stackforge/murano-dashboard
    ..

2.  Create a virtual environment and install dashboard prerequisites. Again,
    we use *tox* for that.

    .. code-block:: console

        $ cd ~/murano/murano-dashboard
        $ tox
    ..

3. Install the latest horizon version and all murano-dashboard requirements into the virtual environment:

   ::

      $ tox -e venv pip install horizon

 It may happen, that the last release of horizon will be not capable with
 latest murano-dashboard code. In that case, horizon need to be installed
 from master branch of this repository: ``https://github.com/openstack/horizon``

4.  Copy configuration file for dashboard.

    .. code-block:: console

        $ cd ~/murano/murano-dashboard/muranodashboard/local
        $ cp local_settings.py.sample local_settings.py
    ..

5.  Edit configuration file.

    .. code-block:: console

        $ cd ~/murano/murano-dashboard/muranodashboard/local
        $ vim ./local_settings.py
    ..

    ::

        ...
        ALLOWED_HOSTS = '*'

        # Provide OpenStack Lab credentials
        OPENSTACK_HOST = '%OPENSTACK_HOST_IP%'

        ...
        # Set secret key to prevent it's generation
        SECRET_KEY = 'random_string'

        ...
        DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
        ...


.. _update_settings:

6. Update settings file


.. _`here`: https://github.com/stackforge/murano-dashboard/blob/master/update_setting.sh

 Running Murano dashboard on developer environment implies the use of murano settings file instead of horizon.
 However, for the correct setup requires settings file to be synchronized with corresponding horizon release.
 But murano-dashboard also have parameters, that should be added to that config. So for your convenience,
 Murano has special script that allows to quickly synchronize Django settings file for a developer installation.
 *update_setting.sh* file can be found `here`_.

 To display all possible options run:

 .. code-block:: console

     ./update_setting.sh --help

 ..

 .. note::

     Ether output or input parameter should be specified.

 ..

* ``--input={PATH/TO/HORIZON/SETTINGS/FILE}`` - settings file to which murano settings would be applied. If omitted, settings from horizon master branch are downloaded.
* ``--output={PATH/TO/FILE}`` - file to store script execution result. Will be overwrite if already exist. If omitted, coincides to the *input* parameter.
* ``--tag`` - horizon release tag name, applied, if no input parameter is provided.
* ``--remove`` - if set, Murano parameters would be removed from the settings file.
* ``--cache-dir={PATH/TO/DIRECTORY}`` - directory to store intermediate script data. Default is */tmp/muranodashboard-cache*.
* ``--log-file={PATH/TO/FILE}`` - file to store the script execution log to a separate file.

7. Run Django server at 127.0.0.1:8000 or provide different IP and PORT parameters.

 .. code-block:: console

     $ cd ~/murano/murano-dashboard
     $ tox -e venv -- python manage.py runserver <IP:PORT>
 ..

 Development server will be restarted automatically on every code change.

8.  Open dashboard using url http://localhost:8000

Import Murano Applications
==========================

Murano provides excellent catalog services, but it also requires applications
which to provide. This section describes how to import Murano Applications from
Murano App Incubator.

1.  Clone Murano App Incubator repository.

    .. code-block:: console

        $ cd ~/murano
        $ git clone https://github.com/murano-project/murano-app-incubator
    ..

2.  Import every package you need from Murano App Incubator using the command
    below.

    .. code-block:: console

        $ cd ~/murano/murano
        $ tox -e venv -- murano-manage \
        > --config-file ./etc/murano/murano.conf \
        > import-package ../murano-app-incubator/%APPLICATION_DIRECTORY_NAME%

.. include:: configure_network.rst
