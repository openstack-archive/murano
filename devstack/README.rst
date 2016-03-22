====================
Enabling in Devstack
====================

#. Download DevStack_::

    git clone https://git.openstack.org/openstack-dev/devstack
    cd devstack

#. Edit local.conf to enable murano devstack plugin::

     > cat local.conf
     [[local|localrc]]
     enable_plugin murano git://git.openstack.org/openstack/murano

#. If you want Murano Cloud Foundry Broker API service enabled, add the
   following line to local.conf::

     enable_service murano-cfapi

#. If you want to use Glare Artifact Repository as a strorage for packages,
   add the following line to ``local.conf``:

   .. code-block:: ini

      enable_service g-glare

   For more information on how to use Glare Artifact Repository,
   see :ref:`glare_usage`.

#. (Optional) To import Murano packages when DevStack is up, define an ordered
   list of packages FQDNs in ``local.conf``. Make sure to list all package
   dependencies. These packages will by default be imported from the murano-apps
   git repository.

   Example::

     MURANO_APPS=io.murano.apps.apache.Tomcat,io.murano.apps.Guacamole

   You can also use the variables ``MURANO_APPS_REPO`` and ``MURANO_APPS_BRANCH``
   to configure the git repository which will be used as the source for the
   imported packages.

#. Install DevStack::

    ./stack.sh


.. _DevStack: http://docs.openstack.org/developer/devstack/
