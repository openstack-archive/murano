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

#. Install DevStack::

    ./stack.sh


.. _DevStack: http://docs.openstack.org/developer/devstack/
