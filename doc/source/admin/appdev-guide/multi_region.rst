.. _multi_region:

Multi-region application
~~~~~~~~~~~~~~~~~~~~~~~~

Since Newton release, Murano supports multi-region application deployment.
All MuranoPL resource classes are inherited from the
``io.murano.CloudResource`` class.
An application developer can set a custom region for ``CloudResource``
subclasses deployment.

Set a region for resources
--------------------------

**To set a region for resources:**

#. Specify a region for  ``CloudResource`` subclasses deployment
   through the ``regionName`` property. For example:

    .. code-block:: yaml

        Application:
          ?:
            type: com.example.apache.ApacheHttpServer
          enablePHP: $.appConfiguration.enablePHP

          ...

          instance:
            ?:
              type: io.murano.resources.LinuxMuranoInstance
            regionName: 'CustomRegion'

            ...

#. Retrieve ``io.murano.CloudRegion`` objects:

    .. code-block:: yaml

        $region: $.instance.getRegion()
        $regionName: $region.name
        $regionLocalStack: $region.stack
        $regionDefaultNetworks: $region.defaultNetworks


As a result, all region-local properties are moved from the ``io.murano.Environment``
class to the new :ref:`cloud-region` class.
For backward compatibility, the ``io.murano.Environment`` class stores
region-specific properties of default region, except the ``defaultNetworks``
in its own properties.
The ``Environment::defaultNetworks`` property contains templates for
the ``CloudRegion::defaultNetworks`` property.

Through current UI, you cannot select networks, flavor, images
and availability zone from a non-default region.
We suggest using regular text fields to specify region-local resources.

Networking and multi-region applications
----------------------------------------

By default, each region has its own separate network.
To ensure connectivity between the networks, create and configure networks in regions
before deploying the application and use ``io.murano.resources.ExistingNeutronNetwork``
to connect the instance to an existing network.
Example:

.. code-block:: yaml

    Application:
      ?:
        type: application.fully.qualified.Name

      ...

      instance_in_region1:
        ?:
          type: io.murano.resources.LinuxMuranoInstance
        regionName: 'CustomRegion1'
        networks:
          useEnvironmentNetwork: false
          useFlatNetwork: false
          customNetworks:
            - ?:
                type: io.murano.resources.ExistingNeutronNetwork
              regionName: 'CustomRegion1'
              internalNetworkName: 'internalNetworkNameInCustomRegion1'
              internalSubnetworkName: 'internalSubNetNameInCustomRegion1'

      instance_in_region2:
        ?:
          type: io.murano.resources.LinuxMuranoInstance
        regionName: 'CustomRegion2'
        networks:
          useEnvironmentNetwork: false
          useFlatNetwork: false
          customNetworks:
            - ?:
                type: io.murano.resources.ExistingNeutronNetwork
              regionName: 'CustomRegion2'
              internalNetworkName: 'internalNetworkNameInCustomRegion2'
              internalSubnetworkName: 'internalSubNetNameInCustomRegion2'

        ...

Also, you can configure networks with the same name and use a template
for the region networks.
That is, describe ``io.murano.resources.ExistingNeutronNetwork`` only once
and assign it to the ``Environment::defaultNetworks::environment`` property.
The environment will create ``Network`` objects for regions from the
``ExistingNeutronNetwork`` template.
Example:

.. code-block:: console

    OS_REGION_NAME="RegionOne" openstack network create <NETWORK-NAME>
    OS_REGION_NAME="RegionTwo" openstack network create <NETWORK-NAME>

    # configure subnets
    #...

    # add ExistingNeutronNetwork to environment object model
    murano environment-create --join-net-id <NETWORK-NAME> <ENV_NAME>

    # also it is possible to specify subnet from <NETWORK-NAME>
    murano environment-create --join-net-id <NETWORK-NAME> --join-subnet-id <SUBNET_NAME> <ENV_NAME>


Additionally, consider the ``[networking]`` section in the configuration
file.
Currently, ``[networking]`` settings are common for all regions.

.. code-block:: ini

   [networking]

   external_network = %EXTERNAL_NETWORK_NAME%
   router_name = %MURANO_ROUTER_NAME%
   create_router = true

If you choose an automatic neutron configuration, configure the external
network with identical names in all regions.
If you disable the automatic router creation, create routers with
identical names in all regions.
Also, the ``default_dns`` address must be reachable from all created networks.

.. note::

    To use regions, first configure them as described in :ref:`multi-region`.
