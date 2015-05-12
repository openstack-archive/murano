.. _use-cases:

.. toctree::
   :maxdepth: 2

=========
Use-cases
=========

Performing application interconnections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Murano can handle application interconnections installed on virtual machines.
The decision of how to combine applications is made by the author of
an application.

To illustrate the way such interconnection can be configured,
let’s analyze the mechanisms applied in WordPress application, which
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

In the ``io.murano.apps.WordPress`` class definition the database property is a
contact for the ``io.murano.databases.MySql`` class. So, the database
configuration methods can be called with the parameters passed by the user
in the main method:

.. code-block:: yaml

   - $.database.createDatabase($.dbName)
   - $.database.createUser($.dbUser, $.dbPassword)
   - $.database.assignUser($.dbUser, $.dbName)

Any other methods of any other class can be invoked the same way to
make the proposal application installation algorithm clear and
constructive. Also, it allows not to duplicate the code in new applications.


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
     type: io.murano.apps.HDPSandbox
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
the application on an Openstack VM. Murano can set up new applications to be managed
by that external load-balancer (LB). Let’s go into more details.

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


