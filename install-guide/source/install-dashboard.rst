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

Install Murano Dashboard
========================

Murano API & Engine services provide the core of Murano. However, your need a
control plane to use it. This section describes how to install and run Murano
Dashboard.

#.  Clone the murano dashboard repository.

    .. code-block:: console

       $ cd ~/murano
       $ git clone git://git.openstack.org/openstack/murano-dashboard
    ..

#.  Clone the ``horizon`` repository

    .. code-block:: console

       $ git clone git://git.openstack.org/openstack/horizon
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
    `horizon documentation <http://docs.openstack.org/developer/horizon/topics/settings.html#openstack-settings-partial>`_.

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
