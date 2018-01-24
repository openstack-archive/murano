.. _use-cases:

=========
Use-cases
=========

Performing application interconnections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Murano can handle application interconnections installed on virtual machines.
The decision of how to combine applications is made by the author of
an application.

To illustrate the way such interconnection can be configured,
let's analyze the mechanisms applied in WordPress application, which
uses MySql.

MySql is a very popular database and can be used in quite a number of various
applications. Instead of the creation of a database inside definition of the
WordPress application, it calls the methods from the MySQL class. At the same
time MySQL remains an independent application.

MySql has a number of methods:

* ``deploy``
* ``createDatabase``
* ``createUser``
* ``assignUser``
* ``getConnectionString``

In the ``com.example.WordPress`` class definition the database property is a
contact for the ``com.example.databases.MySql`` class. So, the database
configuration methods can be called with the parameters passed by the user
in the main method:

.. code-block:: yaml

   - $.database.createDatabase($.dbName)
   - $.database.createUser($.dbUser, $.dbPassword)
   - $.database.assignUser($.dbUser, $.dbName)

Any other methods of any other class can be invoked the same way to
make the proposal application installation algorithm clear and
constructive. Also, it allows not to duplicate the code in new applications.

Abstract dependencies between applications
------------------------------------------
In the example above it is also possible to specify a generic class in the
contract ``com.example.databases.SqlDatabase`` instead of
``com.example.databases.MySql``. It means that an object of any class inherited
from ``com.example.databases.SqlDatabase`` can be passed to a parameter. In
this case you should also use this generic class as a type for a field in
the file ``ui.yaml``:

.. code-block:: yaml

   Forms:
     - appConfiguration:
         fields:
           - name: database
             type: com.example.databases.SqlDatabase
             label: Database Server
             description: >-
               Select a database server to host the application`s database

After that you can choose any database package in a drop-down box.
The last place, which should be changed in the WordPress package to enable this
feature, is manifest file. It should contain the full name of SQL Library
package and optionally packages inherited from SQL library if you want them to
be downloaded as dependencies. For example:

.. code-block:: yaml

   Require:
     com.example.databases:
     com.example.databases.MySql:
     com.example.databases.PostgreSql:

.. note::
   To use this feature you have to enable Glare as a storage for your packages
   and a version of your murano-dashboard should be not older than newton.

Using application already installed on the image
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suppose you have everything already prepared on image. And you want to share this
image with others. This problem can be solved in several ways.

Let's use the
`HDPSandbox <https://github.com/openstack/murano-apps/tree/master/HDPSandbox/package>`_
application to illustrate how this can be done with Murano.

.. note::
   An image may not contain murano-agent at all.

Prepare an application package of the structure:

::

 |_  Classes
 |    |_  HDPSandbox.yaml
 |
 |_  UI
 |    |_  ui.yaml
 |
 |_  logo.png

.. note::

  The ``Resources`` folder is not included in the package since the image
  contains everything that user expects. So no extra instructions are needed
  to be executed on murano-agent.

UI is provided for specifying the application name, which is used for the application
recognition in logging. And what is more, it contains the image name as a deployment
instruction template (object model) in the ``Application`` section:

.. code-block:: yaml
   :linenos:

   Application:
   ?:
     type: com.example.HDPSandbox
   name: $.appConfiguration.name
   instance:
     ?:
       type: io.murano.resources.LinuxMuranoInstance
     name: generateHostname($.instanceConfiguration.unitNamingPattern, 1)
     flavor: $.instanceConfiguration.flavor
     image: 'hdp-sandbox'
     assignFloatingIp: true

Moreover, the unsupported flavors can be specified here, so that the user can
select only from the valid ones. Provide the requirements in the
corresponding section to do this:

.. code-block:: yaml

   requirements:
     min_disk: 50          (Gb)
     min_memory_mb: 4096   (Mb)
     min_vcpus: 1

After the UI form creation, and the HDPSandbox application deployment,
the VM with the predefined image is spawned. Such type of applications may
interact with regular applications. Thus, if you have an image with Puppet,
you can call the ``deploy`` method of the Puppet application and then puppet
manifests or any shell scripts on the freshly spawned VM.

The presence of the logo.png should never be underestimated, since it helps to make
your application recognizable among other applications included in the catalog.

Interacting with non-OpenStack services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section tells about the interaction between an application and any non-OpenStack
services, that have an API.

External load-balancer
----------------------
Suppose, you have powerful load-balancer on a real server. And you want to run
the application on an OpenStack VM. Murano can set up new applications to be managed
by that external load-balancer (LB). Let's go into more details.

To implement this case the following apps are used:

* ``LbApp``:  its class methods call LB API

* ``WebApp``:  runs on the real LB

Several instances of ``WebApp`` are deployed with each of them calling
two methods:

.. code-block:: yaml

  - $.loadBalancer.createPool()
  - $.loadBalancer.addMember($instance)
  # where $.loadBalancer is an instance of the LbApp class

The first method creates a pool and associates it with a virtual server.
This happens once only. The second one registers a member in the newly created pool.

It is also possible to perform other modifications to the LB configuration,
which are only restricted by the LB API functionality.

So, you need to specify the maximum instance number in the UI form related to the
``WebApp`` application. All of them are subsequently added to the LB pool.
After the deployment, the LB virtual IP, by which an application is accessible,
is displayed.

Configuring Network Access for VMs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, each VM instance deployed by ``io.murano.resources.Instance`` class
or its descendants joins an environment's default network. This network gets
created when the Environment is deployed for the first time, a subnet is
created in it and is uplinked to a router which is detected automatically based
on its name.

This behavior may be overridden in two different ways.

Using existing network as environment's default
-----------------------------------------------

This option is available for users when they create a new environment in the
Dashboard. A dropdown control is displayed next to the input field prompting
for the name of environment. By default this control provides to create a new
network, but the user may opt to choose some already existing network to be the
default for the environment being created. If the network has more than one
subnet, the list will include all the available options with their CIDRs
shown. The selected network will be used as environment's default, so no new
network will be created.

.. note::

  Murano does not check the configuration or topology of the network selected
  this way. It is up to the user to ensure that the network is uplinked to some
  external network via a router - otherwise the murano engine will not be able
  to communicate with the agents on the deployed VMs. If the Applications being
  deployed require internet connectivity it is up to the user to ensure that
  this net provides it, than DNS nameservers are set and accessible etc.


Modifying the App UI to prompt user for network
-----------------------------------------------

The application package may be designed to ask user about the network they want
to use for the VMs deployed by this particular application. This allows to
override the default environment's network setting regardless of its value.

To do this, application developer has to include a ``network`` field into the
Dynamic UI definition of the app. The value returned by this field is a tuple
of network_id and a subnet_id. This values may be passed as the
input properties for ``io.murano.resources.ExistingNeutronNetwork`` object
which may be in its turn passed to an instance of
``io.murano.resources.Instance`` as its network configuration.

The UI definition may look like this:

.. code-block:: yaml

  Templates:
    customJoinNet:
      - ?:
          type: io.murano.resources.ExistingNeutronNetwork
        internalNetworkName: $.instanceConfiguration.network[0]
        internalSubnetworkName: $.instanceConfiguration.network[1]
  Application:
    ?:
      type: com.example.someApplicationName
    instance:
      ?:
        type: io.murano.resources.LinuxMuranoInstance
      networks:
        useEnvironmentNetwork: $.instanceConfiguration.network[0]=null
        useFlatNetwork: false
        customNetworks: switch($.instanceConfiguration.network[0], $=null=>list(), $!=null=>$customJoinNet)
  Forms:
    - instanceConfiguration:
        fields:
          - name: network
            type: network
            label: Network
            description: Select a network to join. 'Auto' corresponds to a default environment's network.
            required: false
            murano_networks: translate

For more details on the Dynamic UI its controls and templates please refer to
its :ref:`specification <DynamicUISpec>`.



