====================
Enabling in Devstack
====================

#. Download DevStack_::

    git clone https://git.openstack.org/openstack-dev/devstack
    cd devstack

#. Edit ``local.conf`` to enable murano and heat devstack plugin::

     > cat local.conf
     [[local|localrc]]
     enable_plugin murano https://git.openstack.org/openstack/murano

     #Enable heat plugin
     enable_plugin heat https://git.openstack.org/openstack/heat

#. If you want Murano Cloud Foundry Broker API service enabled, add the
   following line to ``local.conf``::

     enable_service murano-cfapi

#. If you want to use Glare Artifact Repository as a storage for packages,
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

     MURANO_APPS=com.example.apache.Tomcat,org.openstack.Rally

   You can also use the variables ``MURANO_APPS_REPO`` and ``MURANO_APPS_BRANCH``
   to configure the git repository which will be used as the source for the
   imported packages.

#. Install DevStack::

    ./stack.sh


.. _DevStack: https://docs.openstack.org/devstack/latest/
