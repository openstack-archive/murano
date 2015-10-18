====================
Enabling in Devstack
====================

1. Download DevStack

2. Add this repo as an external repository and enable needed services::

     > cat local.conf
     [[local|localrc]]
     enable_plugin murano https://github.com/openstack/murano

3. run ``stack.sh``
