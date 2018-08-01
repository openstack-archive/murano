=====================
Network configuration
=====================

Murano may work in various networking environments and is capable of detecting
the current network configuration and choosing appropriate settings
automatically. However, some additional actions are required to support
advanced scenarios.

Nova-network support
^^^^^^^^^^^^^^^^^^^^

Nova-network is the simplest networking solution, which has limited
capabilities but is available on any OpenStack deployment without the need to
deploy any additional components.

When a new murano environment is created, murano checks if a dedicated
networking service, for example, neutron, exists in the current OpenStack
deployment. It relies on the Identity service catalog for that. If such a
service is not present, murano automatically falls back to nova-network. No
further configuration is needed in this case, all the VMs spawned by Murano
will be joining the same network.

Neutron support
^^^^^^^^^^^^^^^

If neutron is installed, murano enables its advanced networking features that
give you the ability to avoid configuring networks for your application.

By default, it creates an isolated network for each environment and joins
all VMs needed by your application to that network. To install and configure
the application in a newly spawned virtual machine, murano also requires a
router to be connected to the external network.

Automatic neutron configuration
+++++++++++++++++++++++++++++++

To create the router automatically, provide the following parameters in the
configuration file:

.. code-block:: ini

   [networking]

   external_network = %EXTERNAL_NETWORK_NAME%
   router_name = %MURANO_ROUTER_NAME%
   create_router = true

To figure out the name of the external network, run
:command:`openstack network list --external`.

During the first deployment, the required networks and router with a specified
name will be created and set up.

Manual neutron configuration
++++++++++++++++++++++++++++

To configure neutron manually, follow the steps below.

#. Create a public network.

   #. Log in to the OpenStack dashboard as an administrator.

   #. Verify the existence of external networks. For this, navigate to
      :menuselection:`Project > Network > Network Topology`.

   #. Check the network type in network details. For this, navigate to
      :menuselection:`Admin > Networks` and see the :guilabel:`Network name`
      section.
      Alternatively, run the :command:`openstack network list --external`
      command using CLI.

   #. Create a new external network as described in the `OpenStack documentation <http://docs.openstack.org/cli-reference/openstack.html#openstack-network-create>`_.

   .. image:: figures/network-topology-1.png
      :alt: Network Topology page
      :width: 630 px

#. Create a local network.

   #. Navigate to :menuselection:`Project > Network > Networks`.
   #. Click :guilabel:`Create Network` and fill in the form.


#. Create a router.

   #. Navigate to :menuselection:`Project > Network > Routers`.
   #. Click :guilabel:`Create Router`.
   #. In the :guilabel:`Router Name` field, enter *murano-default-router*.
      If you specify a name other than *murano-default-router*, change the
      following settings in the configuration file:

      .. code-block:: ini

         [networking]

         router_name = %SPECIFIED_NAME%
         create_router = false

   #. Click :guilabel:`Create router`.
   #. Click the newly created router name.
   #. In the :guilabel:`Interfaces` tab, click :guilabel:`Add Interface`.
   #. Specify the subnet and IP address.

      .. image:: figures/add-interface.png
         :alt: Add Interface dialog
         :width: 630 px

   #. Verify the result in
      :menuselection:`Project > Network > Network Topology`.

      .. image:: figures/network-topology-2.png
         :alt: Network Topology page
         :width: 630 px
