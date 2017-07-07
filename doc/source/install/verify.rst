.. _verify:

Verify operation
~~~~~~~~~~~~~~~~

Verify operation of the Application Catalog service.

.. note::

   Perform these commands on the controller node.

#. Source the ``admin`` project credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. List service components to verify successful launch and registration
   of each process:

   .. code-block:: console

      $ openstack service list | grep application-catalog
      | 7b12ef5edef848fc9200c271f71b1307 | murano      | application-catalog |