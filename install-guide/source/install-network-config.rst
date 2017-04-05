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

=====================
Network Configuration
=====================
Murano may work in various networking environments and is capable of detecting
the current network configuration and choosing the appropriate settings
automatically. However, some additional actions are required to support
advanced scenarios.

Nova network support
====================
Nova Network is the simplest networking solution, which has limited
capabilities but is available on any OpenStack deployment without the need to
deploy any additional components. For more information about Nova Network, see
`<https://docs.openstack.org/admin-guide/compute-networking-nova.html>`__.

When a new Murano Environment is created, Murano checks if a dedicated
networking service (i.e. Neutron) exists in the current OpenStack deployment.
It relies on Keystone's service catalog for that. If such a service is not
present, Murano automatically falls back to Nova Network. No further
configuration is needed in this case; all the VMs spawned by Murano will join
the same network.

Neutron support
===============
If Neutron is installed, Murano enables its advanced networking features that
give you the ability to not care about configuring networks for your
application.

By default, Murano will create an isolated network for each environment and
attach all VMs needed by your application to that network. To install and
configure applications in just-spawned virtual machines, Murano also requires
a router connected to the external network.

Automatic Neutron network configuration
=======================================
To create a router automatically, provide the following parameters in the
config file:

.. code-block:: ini

   [networking]

   external_network = %EXTERNAL_NETWORK_NAME%
   router_name = %MURANO_ROUTER_NAME%
   create_router = true
..
