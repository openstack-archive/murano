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

#.  Install OpenStack Dashboard, the steps please reference from
    `OpenStack Dashboard Install Guide <https://docs.openstack.org/horizon/latest/install/>`__.

#. Install the packages:

   .. code-block:: console

      # apt install python-murano-dashboard

#. Edit the ``/etc/openstack-dashboard/local_settings.py``
   file to customize local settings of your envi

    .. code-block:: python

        ...
        OPENSTACK_HOST = '%OPENSTACK_HOST_IP%'
        OPENSTACK_KEYSTONE_DEFAULT_ROLE = '%OPENSTACK_ROLE%'
        ...

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

Finalize installation
---------------------

#. Restart the Apache service:

   .. code-block:: console

      # service apache2 restart
