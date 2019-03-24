Install Murano from Source
~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the Application Catalog
service for Ubuntu 16.04 (LTS) from source code.

.. include:: common_prerequisites.rst

Install the API service and Engine
----------------------------------

#.  Create a folder which will hold all Murano components.

    .. code-block:: console

        mkdir ~/murano
    ..

#.  Clone the murano git repository to the management server.

    .. code-block:: console

        cd ~/murano
        git clone https://git.openstack.org/openstack/murano
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

Install Murano Dashboard
========================

Murano API & Engine services provide the core of Murano. However, your need a
control plane to use it. This section describes how to install and run Murano
Dashboard.

#.  Clone the murano dashboard repository.

    .. code-block:: console

       $ cd ~/murano
       $ git clone https://git.openstack.org/openstack/murano-dashboard
    ..

#.  Clone the ``horizon`` repository

    .. code-block:: console

       $ git clone https://git.openstack.org/openstack/horizon
    ..

#.  Create a virtual environment and install ``muranodashboard`` as an editable
    module:

    .. code-block:: console

       $ cd horizon
       $ tox -e venv -- pip install -e ../murano-dashboard
    ..

#.  Prepare local settings.

    .. code-block:: console

       $ cp openstack_dashboard/local/local_settings.py.example \
         openstack_dashboard/local/local_settings.py
    ..

    For more information, check out the official
    `horizon documentation <https://docs.openstack.org/horizon/latest/>`_.

#.  Enable and configure Murano dashboard in the OpenStack Dashboard:

    * For Newton (and later) OpenStack installations, copy the plugin file,
      local settings files, and policy files.

      .. code-block:: console

         $ cp ../murano-dashboard/muranodashboard/local/enabled/*.py \
           openstack_dashboard/local/enabled/

         $ cp ../murano-dashboard/muranodashboard/local/local_settings.d/*.py \
           openstack_dashboard/local/local_settings.d/

         $ cp ../murano-dashboard/muranodashboard/conf/* openstack_dashboard/conf/
      ..

    * For the OpenStack installations prior to the Newton release, run:

      .. code-block:: console

         $ cp ../murano-dashboard/muranodashboard/local/_50_murano.py \
           openstack_dashboard/local/enabled/
      ..

    Customize local settings of your horizon installation, by editing the
    :file:`openstack_dashboard/local/local_settings.py` file:

    .. code-block:: python

        ...
        ALLOWED_HOSTS = '*'

        # Provide OpenStack Lab credentials
        OPENSTACK_HOST = '%OPENSTACK_HOST_IP%'

        ...

        DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
    ..

    Change the default session back end-from using browser cookies to using a
    database instead to avoid issues with forms during the creation of
    applications:

    .. code-block:: python

        DATABASES = {
          'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': 'murano-dashboard.sqlite',
          }
        }

        SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    ..

#.  (Optional) If you do not plan to get the murano service from the keystone
    application catalog, specify where the murano-api service is running:

    .. code-block:: python

        MURANO_API_URL = 'http://%MURANO_IP%:8082'
    ..

#.  (Optional) If you have set up the database as a session back-end (this is
    done by default with the murano local_settings file starting with Newton),
    perform database migration:

    .. code-block:: console

       $ tox -e venv -- python manage.py migrate --noinput
    ..

#.  Run the Django server at 127.0.0.1:8000 or provide different IP and PORT
    parameters:

    .. code-block:: console

       $ tox -e venv -- python manage.py runserver <IP:PORT>
    ..

.. note::

   The development server restarts automatically following every code change.
..

**Result:** The murano dashboard is available at http://IP:PORT.
