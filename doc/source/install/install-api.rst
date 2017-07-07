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

Install Murano API
~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the Application Catalog
service for Ubuntu 14.04 (LTS).

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Install the packages:

   .. code-block:: console

      # apt-get update

      # apt-get install

#. Edit the ``/etc/murano/murano.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://murano:MURANO_DBPASS@controller/murano

Install the API service and Engine
----------------------------------

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
    which contains basic settings you likely need to configure.

    .. note::

        The example below uses SQLite database. Edit **[database]** section
        if you want to use any other database type.
    ..

    .. code-block:: ini

        [DEFAULT]
        debug = true
        verbose = true
        rabbit_host = %RABBITMQ_SERVER_IP%
        rabbit_userid = %RABBITMQ_USER%
        rabbit_password = %RABBITMQ_PASSWORD%
        rabbit_virtual_host = %RABBITMQ_SERVER_VIRTUAL_HOST%
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
    *tox* for that. The virtual environment will be created under *.tox*
    directory.

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
