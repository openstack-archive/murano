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

    sudo apt-get install python-pip python-dev \
      libmysqlclient-dev libpq-dev \
      libxml2-dev libxslt1-dev \
      libffi-dev
..

Fedora
^^^^^^

.. note::

    Fedora support wasn't thoroughly tested. We do not guarantee that murano
    will work on Fedora.
..

.. code-block:: console

    sudo yum install gcc python-setuptools python-devel python-pip
..


CentOS
^^^^^^

.. code-block:: console

    sudo yum install gcc python-setuptools python-devel
    sudo easy_install pip
..


Install tox
-----------

.. code-block:: console

    sudo pip install tox
..


Install And Configure Database
------------------------------

Murano can use various database types on the back end. For development purposes
SQLite is enough in most cases. For production installations you should use
MySQL or PostgreSQL databases.

.. warning::

    Although murano could use a PostgreSQL database on the back end, it wasn't
    thoroughly tested and should be used with caution.
..

To use a MySQL database you should install it and create an empty database first:

.. code-block:: console

    apt-get install python-mysqldb mysql-server
..

.. code-block:: console

    mysql -u root -p

    mysql> CREATE DATABASE murano;
    mysql> GRANT ALL PRIVILEGES ON murano.* TO 'murano'@'localhost' \
        IDENTIFIED BY 'MURANO_DBPASS';
    mysql> exit;
..


Install the API service and Engine
==================================

#.  Create a folder which will hold all Murano components.

    .. code-block:: console

        mkdir ~/murano
    ..

#.  Clone the murano git repository to the management server.

    .. code-block:: console

        cd ~/murano
        git clone git://git.openstack.org/openstack/murano
    ..

#.  Set up the murano config file

    Murano has a common config file for API and Engine services.

    First, generate a sample configuration file, using tox

    .. code-block:: console

        cd ~/murano/murano
        tox -e genconfig
    ..

    And make a copy of it for further modifications

    .. code-block:: console

        cd ~/murano/murano/etc/murano
        ln -s murano.conf.sample murano.conf
    ..

#.  Edit ``murano.conf`` with your favorite editor. Below is an example
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

        ...

        [oslo_messaging_notifications]
        driver = messagingv2

        ...

        [database]
        backend = sqlalchemy
        connection = sqlite:///murano.sqlite

        ...

        [keystone]
        auth_url = 'http://%OPENSTACK_HOST_IP%:5000/v2.0'

        ...

        [keystone_authtoken]
        auth_uri = 'http://%OPENSTACK_HOST_IP%:5000/v2.0'
        auth_host = '%OPENSTACK_HOST_IP%'
        auth_port = 5000
        auth_protocol = http
        admin_tenant_name = %OPENSTACK_ADMIN_TENANT%
        admin_user = %OPENSTACK_ADMIN_USER%
        admin_password = %OPENSTACK_ADMIN_PASSWORD%

        ...

        [murano]
        url = http://%YOUR_HOST_IP%:8082

        [rabbitmq]
        host = %RABBITMQ_SERVER_IP%
        login = %RABBITMQ_USER%
        password = %RABBITMQ_PASSWORD%
        virtual_host = %RABBITMQ_SERVER_VIRTUAL_HOST%

        [networking]
        default_dns = 8.8.8.8 # In case openstack neutron has no default
                              # DNS configured
    ..

#.  Create a virtual environment and install Murano prerequisites. We will use
    *tox* for that. Virtual environment will be created under *.tox* directory.

    .. code-block:: console

        cd ~/murano/murano
        tox
    ..

#.  Create database tables for Murano.

    .. code-block:: console

        cd ~/murano/murano
        tox -e venv -- murano-db-manage \
          --config-file ./etc/murano/murano.conf upgrade
    ..

#.  Open a new console and launch Murano API. A separate terminal is
    required because the console will be locked by a running process.

    .. code-block:: console

        cd ~/murano/murano
        tox -e venv -- murano-api --config-file ./etc/murano/murano.conf
    ..

#.  Import Core Murano Library.

    .. code-block:: console

        cd ~/murano/murano
        pushd ./meta/io.murano
        zip -r ../../io.murano.zip *
        popd
        tox -e venv -- murano --murano-url http://localhost:8082 \
          package-import --is-public io.murano.zip
    ..

#.  Open a new console and launch Murano Engine. A separate terminal is
    required because the console will be locked by a running process.

    .. code-block:: console

        cd ~/murano/murano
        tox -e venv -- murano-engine --config-file ./etc/murano/murano.conf
    ..

Register in Keystone
--------------------

To make the murano API available to all OpenStack users, you need to register the
Application Catalog service within the Identity service.

#. Add ``application-catalog`` service:

   .. code-block:: console

     openstack service create --name murano --description "Application Catalog for OpenStack" application-catalog

#. Provide an endpoint for that service:

   .. code-block:: console

      openstack endpoint create --region RegionOne --publicurl http://<murano-ip>:8082 --internalurl http://<murano-ip>:8082 --adminurl http://<murano-ip>:8082 <MURANO-SERVICE-ID>

   where ``MURANO-SERVICE-ID`` is the unique service number that you can find
   in the :command:`openstack service create` output.

.. note:: URLs (publicurl, internalurl and adminurl) may be different
          depending on your environment.

Install Murano Dashboard
========================

 Murano API & Engine services provide the core of Murano. However, your need a
 control plane to use it. This section describes how to install and run Murano
 Dashboard.

#.  Clone the repository with Murano Dashboard.

    .. code-block:: console

        cd ~/murano
        git clone git://git.openstack.org/openstack/murano-dashboard
    ..

#.  Clone horizon repository

    .. code-block:: console

        git clone git://git.openstack.org/openstack/horizon
    ..

#.  Create venv and install muranodashboard as editable module.

    .. code-block:: console

        cd horizon
        tox -e venv -- pip install -e ../murano-dashboard
    ..

#.  Copy muranodashboard plugin file.

    This step enables murano panel in horizon dashboard.

    .. code-block:: console

        cp ../murano-dashboard/muranodashboard/local/_50_murano.py openstack_dashboard/local/enabled/
    ..

#.  Prepare local settings.

    To get more information, check out official
    `horizon documentation <http://docs.openstack.org/developer/horizon/topics/settings.html#openstack-settings-partial>`_.

    .. code-block:: console

        cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py

#.  Customize local settings according to OpenStack installation.

    .. code-block:: python

        ...
        ALLOWED_HOSTS = '*'

        # Provide OpenStack Lab credentials
        OPENSTACK_HOST = '%OPENSTACK_HOST_IP%'

        ...

        # Set secret key to prevent it's generation
        SECRET_KEY = 'random_string'

        ...

        DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
    ..

    Also, it's better to change default session backend from  browser cookies to database to avoid
    issues with forms during creating applications:

    .. code-block:: python

        ...
        DATABASES = {
            'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'murano-dashboard.sqlite',
            }
        }

        SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    ..

    If you do not plan to get murano service from keystone application catalog,
    provide where murano-api service is running:

    .. code-block:: python

        ...
        MURANO_API_URL = 'http://localhost:8082'
    ..

#.  Perform database synchronization.

    Optional step. Needed in case you set up database as a session backend.

    .. code-block:: console

        tox -e venv -- python manage.py migrate --noinput
    ..

    You can reply 'no' since for development purpose separate user is not needed.

#.  Run Django server at 127.0.0.1:8000 or provide different IP and PORT parameters.

    .. code-block:: console

        tox -e venv -- python manage.py runserver <IP:PORT>
    ..

    Development server will be restarted automatically on every code change.

#.  Open dashboard using url http://localhost:8000

Import Murano Applications
==========================

Applications need to be imported
to fill the catalog. This can be done via the dashboard, and via CLI:

1.  Clone the murano apps repository.

    .. code-block:: console

        cd ~/murano
        git clone git://git.openstack.org/openstack/murano-apps
    ..

2.  Import every package you need from this repository, using the command
    below.

    .. code-block:: console

        cd ~/murano/murano
        pushd ../murano-apps/Docker/Applications/%APP-NAME%/package
        zip -r ~/murano/murano/app.zip *
        popd
        tox -e venv -- murano --murano-url http://localhost:8082 package-import app.zip

.. include:: configure_network.rst
