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
service for Ubuntu 16.04 (LTS).

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

#. Install the packages:

   .. code-block:: console

      # apt-get update

      # apt-get install murano-engine murano-api

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
        connection = mysql+pymysql://murano:MURANO_DBPASS@controller/murano

        ...

        [keystone]
        auth_url = 'http://%OPENSTACK_HOST_IP%:5000/v2.0'

        ...

        [keystone_authtoken]
        www_authenticate_uri = 'http://%OPENSTACK_HOST_IP%:5000/v2.0'
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

#. Populate the Murano database:

   .. code-block:: console

      # su -s /bin/sh -c "murano-db-manage upgrade" murano

   .. note::

      Ignore any deprecation messages in this output.

Finalize installation
---------------------

#. Restart the Application Catalog services:

   .. code-block:: console

      # service murano-api restart
      # service murano-engine restart
