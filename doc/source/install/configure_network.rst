..
    Copyleft 2014 Mirantis, Inc.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.
..

Network Configuration
---------------------

To work with Murano, tenant network in Openstack installation should be configured in a certain way.
This configuration may be set up automatically with the provision of several parameters in config file or manually.

Murano has advanced networking features that give you ability to not care about configuring networks
for your application. By default it will create an isolated network for each environment and join
all VMs needed by your application to that network. To install and configure application in
just spawned virtual machine Murano also requires a router connected to the external network.


Automatic network configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create router automatically, provide the following parameters in config file:

.. code-block:: ini

    [networking]

    external_network = %EXTERNAL_NETWORK_NAME%
    router_name = %MURANO_ROUTER_NAME%
    create_router = true

..

To figure out the name of the external network, perform the following command:

.. code-block:: console

    $ neutron net-external-list

During the first deploy, required networks and router with specified name will be created and set up.

Manual network configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Step 1. Create public network

 * First, you need to check for existence of external networks. Login as admin and go to
   *Project -> Network -> Network Topology*. And check network type in network details at *Admin -> Networks -> Network name* page.
   The same action can be done via CLI by running `neutron net-external-list`. To create new external network examine `OpenStack documentation <http://docs.openstack.org/trunk/install-guide/install/apt/content/neutron_initial-external-network.html>`_.

  .. image:: 1.png
     :align: left
     :scale: 70 %

* Step 2. Create local network

 * Go to *Project -> Network -> Networks*.
 * Click *Create Network* and fill the form.

  .. image:: 2.png


  .. image:: 3.png

* Step 3. Create router

 * Go to *Project -> Network -> Routers*

 * Click "Create Router"
 * In the "Router Name" field, enter the *murano-default-router*

  .. image:: 4_1.png


  If you specify a name other than *murano-default-router*, it will be necessary to change the following settings in the config file:

  .. code-block:: ini

     [networking]

     router_name = %SPECIFIED_NAME%
     create_router = false


 * Click on the specified router name
 * In the opened view click “Add interface”
 * Specify the subnet and IP address

  .. image:: 4_2.png

  And check the result in `Network Topology` tab.

  .. image:: 5.png
