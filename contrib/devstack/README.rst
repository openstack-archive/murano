1. Follow Devstack documentation to setup a host for Devstack. Then clone
   Devstack source code.

2. Copy Murano integration scripts to Devstack either by setting environment
   variable or providing complete path to devstack directory. Below one is using
   environment variable::

      $ export DEVSTACK_DIR=<complete path to devstack directory(clonned)>
      $ cp lib/murano ${DEVSTACK_DIR}/lib
      $ cp lib/murano-dashboard ${DEVSTACK_DIR}/lib
      $ cp extras.d/70-murano.sh ${DEVSTACK_DIR}/extras.d

3. Create a ``localrc`` file as input to devstack.

4. The Murano, Neutron and Heat services are not enabled by default, so they must 
   be enabled in ``localrc`` before running ``stack.sh``. This example ``localrc``
   file shows all of the settings required for Murano::

      # Enable Neutron
      ENABLED_SERVICES+=,q-svc,q-agt,q-dhcp,q-l3,q-meta,neutron

      # Enable Heat
      enable_service heat h-api h-api-cfn h-api-cw h-eng

      # Enable Murano
      enable_service murano murano-api murano-engine

5. Deploy your OpenStack Cloud with Murano::

   $ ./stack.sh
