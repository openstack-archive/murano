.. _configure_service_broker:

.. toctree::
   :maxdepth: 2

=======================================
Murano service broker for Cloud Foundry
=======================================

Service broker overview
-----------------------

Service broker is a new murano component which implements `Cloud Foundry
<https://www.cloudfoundry.org/>`_ Service Broker API.

This lets users build ‘hybrid’ infrastructures that are services like databases, message
queues, key/value stores, and so on. This services can be uploaded and deployed with
murano and made available to Cloud Foundry apps on demand. The result is lowered cost,
shorter timetables, and quicker access to required tools — developers can ‘self serve’
by building any required service, then make it instantly available in Cloud Foundry.

Configure service broker
------------------------

Manual installation
~~~~~~~~~~~~~~~~~~~

If you use local murano installation, you can configure and run murano service
broker in a few simple steps:

#.  Add new entry to the murano configuration file.

    .. code-block:: ini

        [cfapi]
        tenant = %TENANT_NAME%
        bind_host = %HOST_IP%
        bind_port = 8083
        auth_url = 'http://%OPENSTACK_HOST_IP%:5000/v2.0'

    .. note::

        bind_host IP should be in the same network as Cloud Foundry instance


#.  Open a new console and launch service broker.

    .. code-block:: console

        cd ~/murano/murano
        tox -e venv -- murano-cfapi --config-file ./etc/murano/murano.conf

Devstack installation
~~~~~~~~~~~~~~~~~~~~~

It is really easy to enable service broker in your devstack installation.
You need simply update your :file:`local.conf` with the following:

    .. code-block:: ini

       [[local|localrc]]
       enable_plugin murano git://git.openstack.org/openstack/murano
       enable_service murano-cfapi

How to use service broker
-------------------------

After service broker is configured and started you have nothing to do with service
broker from murano side - it is an adapter which is used by Cloud Foundry PaaS.

To access and use murano packages through Cloud Foundry, you need to perform following steps:

#. Log in to Cloud Foundry instance via ssh.

   .. code-block:: console

      ssh -i <key_name> <username>@<hostname>

#. Log in to Cloud Foundry itself.

   .. code-block:: console

      cf login -a https://api.<smthg>.xip.io -u <user_name> -p <password>

#. Add murano service broker.

   .. code-block:: console

      cf create-service-broker <broker_name> <OS_USERNAME> <OS_PASSWORD>  http://<service_broker_ip>:8083

#. Enable access to murano packages.

   .. code-block:: console

      cf enable-service-access <service_name>

   .. warning::

      By default, access to all services is prohibited.

   .. note::

      You can use `service-access` command to see human-readable list of packages.

#. Provision murano service through Cloud Foundry.

   .. code-block:: console

      cf create-service 'Apache HTTP Server' default MyApacheInstance  -c apache.json

   .. code-block:: json

      {
          "instance": {
              "flavor": "m1.medium",
              "?": {
                  "type": "io.murano.resources.LinuxMuranoInstance"
              },
              "keyname": "nstarodubtsev",
              "assignFloatingIp": "True",
              "name": <name_pattern>,
              "availabilityZone": "nova",
              "image": "1b9ff37e-dff3-4308-be08-9185705dad91"
          },
          "enablePHP": "True"
      }

Known issues
------------

* `Hard to deploy complex apps
  <https://bugs.launchpad.net/murano/+bug/1500777>`_

Useful links
------------

Here is the list of the links for Cloud Foundry documentation which you might need:

#.  `Cloud Foundry development version launcher
    <https://github.com/yudai/cf_nise_installer>`_

#.  `How to manage Cloud Foundry service brokers
    <https://docs.cloudfoundry.org/services/managing-service-brokers.html>`_

#. `Cloud Foundry CLI docs
   <http://docs.cloudfoundry.org/devguide/#cf>`_
