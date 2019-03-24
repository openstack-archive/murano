.. _install_manually:

=======================
Install murano manually
=======================

Before you install Murano, verify that you completed the following tasks:

#. Install software prerequisites depending on the operating system you use
   as described in the System prerequisites section.

   .. TODO (OG): add ref to System prerequisites when it is ready

#. Install tox:

   .. code-block:: console

      sudo pip install tox

#. Install and configure a database.

   Murano can use various database types on back end. For development
   purposes, use SQLite. For production installations, consider using
   MySQL database.

   .. warning::

      Murano supports PostgreSQL as well. Though, use it with caution
      as it has not been thoroughly tested yet.

   Before you can use MySQL database, proceed with the following:

   #. Install MySQL:

      .. code-block:: console

         apt-get install mysql-server

   #. Create an empty database:

      Replace %MURANO_DB_PASSWORD% with the actual password. For example,
      'admin'.

      .. code-block:: console

         mysql -u root -p

         mysql> CREATE DATABASE murano;
         mysql> GRANT ALL PRIVILEGES ON murano.* TO 'murano'@'localhost' \
         IDENTIFIED BY %MURANO_DB_PASSWORD%;
         mysql> exit;

Install the API service and engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#.  Create a folder to which all murano components will be stored:

    .. code-block:: console

        mkdir ~/murano

#.  Clone the murano git repository to the management server:

    .. code-block:: console

        cd ~/murano
        git clone https://git.openstack.org/openstack/murano

#.  Create the configuration file. Murano has a common configuration
    file for API and engine services.

    #. Generate a sample configuration file using tox:

       .. code-block:: console

          cd ~/murano/murano
          tox -e genconfig

    #. Create a copy of ``murano.conf`` for further modifications:

       .. code-block:: console

          cd ~/murano/murano/etc/murano
          cp murano.conf.sample murano.conf

#.  Edit the ``murano.conf`` file. An example below contains the basic
    configuration.

    .. note::

       The example uses MySQL database. If you want to use another
       database type, edit the ``[database]`` section correspondingly.

       Replace items in "%" with the actual values. For example, replace
       %RABBITMQ_SERVER_IP% with 127.0.0.1. So, the complete row with the
       replaced value will be rabbit_host = 127.0.0.1

    .. code-block:: ini

        [DEFAULT]
        debug = true
        verbose = true
        rabbit_host = %RABBITMQ_SERVER_IP%
        rabbit_userid = %RABBITMQ_USER%
        rabbit_password = %RABBITMQ_PASSWORD%
        rabbit_virtual_host = %RABBITMQ_SERVER_VIRTUAL_HOST%

        ...

        [database]
        connection = mysql+pymysql://murano:%MURANO_DB_PASSWORD%@127.0.0.1/murano

        ...

        [keystone]
        auth_url = 'http://%OPENSTACK_HOST_IP%:5000'

        ...

        [keystone_authtoken]
        www_authenticate_uri  = 'http://%OPENSTACK_HOST_IP%:5000'
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
        default_dns = 8.8.8.8 # In case OpenStack neutron has no default
                              # DNS configured

        [oslo_messaging_notifications]
        driver = messagingv2

#. Create a virtual environment and install murano prerequisites
   using **tox**. The virtual environment will be created under
   the ``tox`` directory.

   #. Install MySQL driver since it is not a part of the murano requirements:

      .. code-block:: console

         tox -e venv -- pip install PyMYSQL

   #. Create database tables for murano:

      .. code-block:: console

         cd ~/murano/murano
         tox -e venv -- murano-db-manage \
         --config-file ./etc/murano/murano.conf upgrade

   #.  Launch the murano API in a separate terminal:

       .. code-block:: console

          cd ~/murano/murano
          tox -e venv -- murano-api --config-file ./etc/murano/murano.conf

       .. note::

          Run the command in a new terminal as the process will be running in
          the terminal until you terminate it, therefore, blocking the current
          terminal.

   #.  Leaving the API process running, return to the previous console and
       import murano core library and other libraries from the `meta`
       directory:

       .. code-block:: console

          cd ~/murano/murano/meta/
          for i in */; do pushd ./"$i"; zip -r ../../"${i%/}.zip" *; popd; done
          cd ..
          tox -e venv -- murano --os-username %OPENSTACK_ADMIN_USER% \
          --os-password %OPENSTACK_ADMIN_PASSWORD% \
          --os-auth-url http://%OPENSTACK_HOST_IP%:5000 \
          --os-project-name %OPENSTACK_ADMIN_TENANT% \
          --murano-url http://%MURANO_IP%:8082 \
          package-import --is-public *.zip
          rm *.zip

   #.  Launch the murano engine in a separate terminal:

       .. code-block:: console

          cd ~/murano/murano
          tox -e venv -- murano-engine --config-file ./etc/murano/murano.conf

       .. note::

          Run the command in a new terminal as the process will be running in
          the terminal until you terminate it, therefore, blocking the current
          terminal.

Register in keystone
~~~~~~~~~~~~~~~~~~~~

To make the murano API available to all OpenStack users, you need to register
the Application Catalog service within the Identity service.

#. Add the ``application-catalog`` service to keystone:

   .. code-block:: console

      openstack service create --name murano --description \
      "Application Catalog for OpenStack" application-catalog

#. Provide an endpoint for this service:

   .. code-block:: console

      openstack endpoint create --region RegionOne --publicurl 'http://%MURANO_IP%:8082/' \
      --adminurl 'http://%MURANO_IP%:8082/' --internalurl 'http://%MURANO_IP%:8082/' \
      %MURANO_SERVICE_ID%

   where ``MURANO-SERVICE-ID`` is the unique service number that can be found
   in the :command:`openstack service create` output.

  .. note::

     URLs (``--publicurl``, ``--internalurl``, and ``--adminurl`` values)
     may differ depending on your environment.

Install the murano dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and run the murano dashboard.

#.  Clone the repository with the murano dashboard:

    .. code-block:: console

        cd ~/murano
        git clone https://git.openstack.org/openstack/murano-dashboard

#.  Clone the ``horizon`` repository:

    .. code-block:: console

       git clone https://git.openstack.org/openstack/horizon

#.  Create a virtual environment and install ``muranodashboard``
    as an editable module:

    .. code-block:: console

        cd horizon
        tox -e venv -- pip install -e ../murano-dashboard

#.  Prepare local settings.

    .. code-block:: console

        cp openstack_dashboard/local/local_settings.py.example \
        openstack_dashboard/local/local_settings.py


    For more information, check out the official
    `horizon documentation <https://docs.openstack.org/horizon/latest/>`_.

#.  Enable and configure Murano dashboard in the OpenStack Dashboard:

    * For the Newton (and later) OpenStack installations, copy plug-in file
      local settings files, and policy files:

      .. code-block:: console

         cp ../murano-dashboard/muranodashboard/local/enabled/*.py \
         openstack_dashboard/local/enabled/

         cp ../murano-dashboard/muranodashboard/local/local_settings.d/*.py \
         openstack_dashboard/local/local_settings.d/

         cp ../murano-dashboard/muranodashboard/conf/* openstack_dashboard/conf/

    * For the OpenStack installations prior to the Newton release, run:

      .. code-block:: console

         cp ../murano-dashboard/muranodashboard/local/_50_murano.py \
         openstack_dashboard/local/enabled/

      Customize local settings of your horizon installation, by editing the
      ``openstack_dashboard/local/local_settings.py`` file:

      .. code-block:: python

         ...
         ALLOWED_HOSTS = '*'

         # Provide your OpenStack Lab credentials
         OPENSTACK_HOST = '%OPENSTACK_HOST_IP%'

         ...

         DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

      Change the default session back end from browser cookies to database
      to avoid issues with forms during the applications creation:

      .. code-block:: python

         DATABASES = {
           'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': 'murano-dashboard.sqlite',
           }
         }

         SESSION_ENGINE = 'django.contrib.sessions.backends.db'


#. (Optional) If you do not plan to get the murano service from the keystone
   application catalog, specify where the ``murano-api`` service is running:

    .. code-block:: python

       MURANO_API_URL = 'http://%MURANO_IP%:8082'

#. (Optional) If you have set up the database as a session back end (this is
   done by default with murano local_settings file starting with Newton),
   perform database migration:

   .. code-block:: console

      tox -e venv -- python manage.py migrate --noinput

   Since a separate user is not required for development purpose,
   you can reply ``no``.

#.  Run Django server at ``127.0.0.1:8000`` or provide a different ``IP``
    and ``PORT`` parameters:

    .. code-block:: console

       tox -e venv -- python manage.py runserver <IP:PORT>

    .. note::

       The development server restarts automatically on every code change.

**Result:** The murano dashboard is available at ``http://IP:PORT``.

Import murano applications
~~~~~~~~~~~~~~~~~~~~~~~~~~

To fill the application catalog, you need to import applications to your
OpenStack environment. You can import applications using the murano dashboard,
as well as the command-line client.

To import applications using CLI, complete the following tasks:

#. Clone the murano apps repository:

   .. code-block:: console

      cd ~/murano
      git clone https://git.openstack.org/openstack/murano-apps

#. Import every package you need from this repository by running
   the following command:

   .. code-block:: console

      cd ~/murano/murano
      pushd ../murano-apps/Docker/Applications/%APP-NAME%/package
      zip -r ~/murano/murano/app.zip *
      popd
      tox -e venv -- murano --murano-url http://%MURANO_IP%:8082 package-import app.zip

**Result:** The applications are imported and available from the application
catalog.
