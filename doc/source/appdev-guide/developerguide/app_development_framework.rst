.. _app-development-framework:

=================================
Application development framework
=================================

Application development framework is a library that helps application
developers to create applications that can be scalable, highly available,
(self)healable and do not contain boilerplate code for common application
workflow operations. This library is placed into the Murano repository under
the ``meta/io.murano.applications`` folder.

To allow your applications to use the code of the library, zip it and upload
to the Murano application catalog.

Framework objectives
--------------------

The library allows application developers to focus on their
application-specific tasks without the real need to dive into resource
orchestration, server farm configuration, and so on. For example, on how to
install the software on the VMs, how to configure it to interact with other
applications. Application developers are able to focus more on the software
configuration tools (scripts, puppets, and others) and care less about the
MuranoPL if they do not need to define any custom workflow logic.

The main capabilities the library provides and its main use-cases are as
follows:

* Standard operations are implemented in the framework and can be left as is
* The capability to create multi-server applications and scale them
* The capability to create composite multi-component applications
* The capability to track application failures and recover from them
* The capability to define event handlers for various events

Quickstart
----------

To use the framework in your application, include the following lines to the
``manifest.yaml`` file:

.. code-block:: yaml

   Require:
    io.murano.applications:

Create a one-component single-server application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**To create a simple application deployed on a single server**:

#. Include the following lines to the code of the application class:

   .. code-block:: yaml

      Namespaces:
        =: my.new.ns
        apps: io.murano.applications

      Name: AppName
      Extends: apps:SingleServerApplication


#. Provide an input for the application ``server`` property in your
   ``ui.yaml`` file:

   .. code-block:: yaml

      Application:
        ?:
          type: my.new.ns.AppName
        server:
          ?:
            type: io.murano.resources.LinuxMuranoInstance
          name: generateHostname($.instanceConfiguration.unitNamingPattern, 1)
          flavor: $.instanceConfiguration.flavor
          ... <other instance properties>


   Now you already have the app that creates a server ready for installing
   software on it.

#. To create a fully functional app, add an installation script to the body
   of the ``onInstallServer`` method:

   .. code-block:: yaml

      Methods:
        onInstallServer:
          Arguments:
            - server:
                Contract: $.class(res:Instance).notNull()
            - serverGroup:
                Contract: $.class(apps:ServerGroup).notNull()
          Body:
            - $file: sys:Resources.string('installScript.sh')
            - conf:Linux.runCommand($server.agent, $file)


#. Optional. Add other methods that handle certain stages of the application
   workflow, such as ``onBeforeInstall``, ``onCompleteInstallation``,
   ``onConfigureServer``, ``onCompleteConfiguration``, and others. For details
   about these methods, see the
   :ref:`Software components <software-components>` section.

Create a one-component multi-server application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**To create an application that is intended to be installed on several servers**:

#. Make it inherit the ``MultiServerApplication`` class:

   .. code-block:: yaml

      Namespaces:
        =: my.new.ns
        apps: io.murano.applications

      Name: AppName
      Extends: apps:MultiServerApplication


#. Instead of the ``server`` property in ``SingleServerApplication``, provide
   an input for the ``servers`` property that accepts the instance of one of
   the inheritors of the ``ServerGroup`` class. The ``ui.yaml`` file in this
   case may look as follows:

   .. code-block:: yaml

      Application:
        ?:
          type: my.new.ns.AppName
        servers:
          ?:
            type: io.murano.applications.ServerList
          servers:
            - ?:
                type: io.murano.resources.LinuxMuranoInstance
              name: "Server-1"
              flavor: $.instanceConfiguration.flavor
              ... <other instance properties>

            - ?:
                type: io.murano.resources.LinuxMuranoInstance
              name: "Server-2"
              flavor: $.instanceConfiguration.flavor
              ... <other instance properties>


#. Define the custom logic of the application in the handler methods, and it
   will be applied to the whole app, exactly like with
   ``SingleServerApplication``.

Create a scalable multi-server application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**To provide the application with the ability to scale**:

#. Make the app extend the ``MultiServerApplicationWithScaling`` class:

   .. code-block:: yaml

      Namespaces:
        =: my.new.ns
        apps: io.murano.applications

      Name: AppName
      Extends: apps:MultiServerApplicationWithScaling

#. Provide the ``ui.yaml`` file:

   .. code-block:: yaml

      Application:
        ?:
          type: my.new.ns.AppName
        servers:
          ?:
            type: io.murano.applications.ServerReplicationGroup
          numItems: $.appConfiguration.numNodes
          provider:
            ?:
              type: io.murano.applications.TemplateServerProvider
            template:
              ?:
                type: io.murano.resources.LinuxMuranoInstance
              flavor: $.instanceConfiguration.flavor
              ... <other instance properties>
            serverNamePattern: $.instanceConfiguration.unitNamingPattern


   The ``servers`` property accepts instance of the ``ServerReplicationGroup``
   class, and in turn it requires input of the ``numItems`` and ``provider``
   properties.

After the deployment, the ``scaleOut`` and ``scaleIn`` public methods
(actions) become available in the dashboard UI.

For a working example of such application, see the
``com.example.apache.ApacheHttpServer`` package version 1.0.0.


Library overview
----------------

The framework includes several groups of classes:

  ``replication.yaml``
    Classes that provide the capability to replicate the resources.

  ``servers.yaml``
    Classes that provide instances grouping and replication.

  ``component.yaml``
    Classes that define common application workflows.

  ``events.yaml``
    Class for handling events.

  ``baseapps.yaml``
    Base classes for applications.

As it is described in the :ref:`Quickstart` section, the application makes use
of the Application development framework by inheriting from one of the base
application classes, such as ``SingleServerApplication``,
``MultiServerApplication``, ``MultiServerApplicationWithScaling``. In turn,
these classes are inheritors of the standard ``Application`` class and the
``SoftwareComponent`` class. The latter class binds all of the framework
capabilities.

The ``SoftwareComponent`` class inherits both ``Installable`` and
``Configurable`` classes which provide boilerplate code for the installation
and configuration workflow respectively. They also contain empty methods
for each stage of the workflow (e.g. ``onBeforeInstall``, ``onInstallServer``),
which are the places where application developers can add their own
customization code.

The entry point to execute deployment of the software component is its
``deployAt`` method which requires instance of one of the inheritors of the
``serverGroup``  class. It is the object representing the group of servers
the application should be deployed to. The application holds such an object as
one of its properties. It can be a single server (``SingleServerGroup``
subclass), a prepopulated list of servers (``ServerList`` subclass) or a list
of servers that are dynamically generated in runtime
(``ServerReplicationGroup`` subclass).

``ServerReplicationGroup`` or, more precisely, one of its parent classes
``ReplicationGroup`` controls the number of items it holds by releasing items
over the required amount and requesting creation of the new items in runtime
from the ``ReplicaProvider`` class which acts like an object factory. In case
of servers, it is ``TemplateServerProvider`` which creates new servers from the
given template. Replication is done during the initial deployment and during
the scaling actions execution.

Framework detailed description
------------------------------

This section provides technical description of all the classes present in the
application development library, their hierarchy and usage.

Scaling primitives
~~~~~~~~~~~~~~~~~~

There is an ability to group similar resources together, produce new copies
of the same resources or release the existing ones on request. Now it is
implemented for instances only, other resources may be added later.

The following is the hierarchy of classes that provide grouping and
replication of resources:

::

 +-------+
 | +-------+
 | | +--------+        +------------------+        +-----------------+
 | | |        |        |                  |        |                 |
 +-+ | Object <--------+ ReplicationGroup +--------> ReplicaProvider |
   +-+        |        |                  |        |                 |
     +--------+        +---+--------------+        +-+--------+------+
                           ^                         ^        ^
                           |                         |        |
                           |      +------------------+-----+  |
                           |      |                        |  |
 +-------+                 |      |  CloneReplicaProvider  |  |
 | +-------+               |      |        + other         |  |
 | | +----------+          |      +------------------------+  |
 | | |          |          |                                  |
 +-+ | Instance |          |                                  |
   +-+          |          |                                  |
     +----+-----+          |                                  |
          |                |                                  |
    +-----+-------+        |                                  |
    |             |        |                                  |
    | ServerGroup |        |                  +---------------+--+
    |             |        |                  |     Template     |
    +-----^-------+    +---+----------+       |      Server      +--+
          |            |    Server    +------->     Provider     |  |
          +------------+  Replication |       +-----+------------+  +---+
                       |    Group     |             |               |   |
                       +--------------+             +---+---other---+   |
                                                        |               |
                                                        +---------------+


**ReplicationGroup**

    A base class which holds the collection of objects generated in runtime in
    its ``items`` output property and contains a reference to a
    ``ReplicaProvider`` object in its ``provider`` property which is used to
    dynamically generate the objects in runtime.

    Input properties of this class include the ``minItems`` and ``maxItems``
    allowing to limit the number of objects it holds in its collection.

    An input-output property ``numItems`` allows to declaratively change the
    set of objects in the collection by setting its size.

    The ``deploy()`` method is used to apply the replica settings: it drops
    the objects from the collection if their number exceeds the number
    specified by the ``numItems`` or generate some new if there are not enough
    of them.

    The ``scale()`` method is used to increase or decrease the ``numItems`` by
    some number specified in the ``delta`` argument of the method, but in
    range between ``maxItems`` and ``minItems``.

**ReplicaProvider**

    A class which does the object replication. The base one is abstract, its
    inheritors should implement the abstract ``createReplica`` method to
    create the actual object. The method accepts the ``index`` parameter to
    properly parametrize the newly created copy and optional ``owner``
    parameter to use it as an owner for the newly created objects.

    The concrete implementations of this class should define all the input
    properties needed to create new instances of object. Thus the provider
    actually acts as a template of the object it generates.

**CloneReplicaProvider**

    An implementation of ``ReplicaProvider`` capable to create replicas by
    cloning some user-provided object, making use of the ``template()``
    contract.

**PoolReplicaProvider**

    Replica provider that takes replicas from the prepopulated pool instead
    of creating them.

**RoundrobinReplicaProvider**

    Replica provider with a load balancing that returns replica from the
    prepopulated list. Once the provider runs out of free items it goes to the
    beginning of the list and returns the same replicas again.

**CompositeReplicaProvider**

    Replica provider which is a composition of other replica providers. It
    holds the collection of providers in its ``providers`` input property.
    Its ``ReplicaProvider`` method returns a new replica created by the first
    provider in that list. If that value is `null`, the replica created by the
    second provider is returned, and so on. If no not-null replicas are
    created by all providers, the method returns null.

    This provider can be used to have some default provider with the ability
    to fall back to the next options if the preferable one is not successful.


Servers replication
~~~~~~~~~~~~~~~~~~~

**ServerGroup**

    A class that provides static methods for deployment and releasing
    resources on the group of instances.

    The ``deployServers()`` static method accepts instance of ``ServerGroup``
    class and a list of servers as the parameters and deploys all servers from
    the list in the environment which owns the server group, unless server is
    already deployed.

    The ``releaseServers()`` static method accepts a list of servers as the
    parameter and consequentially calls ``beginReleaseResources()`` and
    ``endReleaseResources()`` methods on each server.

**ServerList**

    A class that extends the ``ServerGroup`` class and holds a group of
    prepopulated servers in its ``servers`` input property.

    The ``deploy()`` method calls the ``deployServers()`` method with the
    servers defined in the ``servers`` property.

    The ``.destroy()`` method calls the ``releaseServers()`` method with the
    servers defined in the ``servers`` property.

**SingleServerGroup**

    Degenerate case of a ``ServerGroup`` which consists of a single server.
    Has the ``server`` input property to hold a single server.

**CompositeServerGroup**

    A server group that is composed of other server groups.

**ServerReplicationGroup**

    A subclass of the ``ReplicationGroup`` class and the ``ServerGroup``
    class to replicate the ``Instance`` objects it holds.

    The ``deploy()`` method of this group not only generates new instances of
    servers but also deploys them if needed.

**TemplateServerProvider**

    A subclass of ``ReplicaProvider`` which is used to produce the objects
    of one of the ``Instance`` class inheritors by creating them from the
    provided template with parameterization of the hostnames. The resulting
    hostname looks like 'Server {index}{groupName}'.

    May be passed as ``provider`` property to objects of the
    ``ServerReplicationGroup`` class.

**other replica providers**

    Other subclasses of ``ReplicaProvider`` may be created to produce different
    objects of ``Instance`` class and its subclasses depending on particular
    application needs.


Classes for grouping and replication of other kinds of resources are to be
implemented later.

.. _software-components:

Software Components
~~~~~~~~~~~~~~~~~~~

The class to handle the lifecycle of the application is the
``SoftwareComponent`` class which is a subclass of ``Installable`` and
``Configurable``:

::

 +-----------+-+           +-+------------+
 |             |           |              |
 | Installable |           | Configurable |
 |             |           |              |
 +-----------+-+           +-+------------+
             ^               ^
             |               |
             |               |
           +-+---------------+-+
           |                   |
           | SoftwareComponent |
           |                   |
           +-------------------+


The hierarchy of the ``SoftwareComponent`` classes is used to define the
workflows of different application lifecycles. The general logic of the
application behaviour is contained in the methods of the base classes and
the derived classes are able to implement the handlers for the custom logic.
The model is event-driven: the workflow consists of the multiple steps, and
most of the steps invoke appropriate `on%StepName%` methods intended to
provide application-specific logic.

Now 'internal' steps logic and their 'public' handlers are split into the
separate methods. It should improve the developers' experience and simplify
the code of the derived classes.

The standard workflows (such as Installation and Configuration) are defined
by the ``Installable`` and ``Configurable`` classes respectively. The
``SoftwareComponent`` class inherits both these classes and defines its
deployment workflow as a sequence of Installation and Configuration flows.
Other future implementations may add new workflow interfaces and mix them in
to change the deployment workflow or add new actions.

**Installation** workflow consists of the following methods:

::

 +----------------------------------------------------------------------------------------------------------------------+
 | INSTALL                                                                                                              |
 |                                                                                                                      |
 |      +------------------------------+                               +---------------+                                |
 |    +------------------------------+ |                             +---------------+ |                                |
 |  +------------------------------+ | |      +---------------+    +---------------+ | |      +----------------------+  |
 |  |                              | | |      |               |    |               | | |      |                      |  |
 |  |    checkServerIsInstalled    | +-+ +----> beforeInstall +----> installServer | +-+ +----> completeInstallation |  |
 |  |                              +-+        |               |    |               +-+        |                      |  |
 |  +------------------------------+          +------+--------+    +------+--------+          +-----------+----------+  |
 |                                                   |                    |                               |             |
 +----------------------------------------------------------------------------------------------------------------------+
                                                     |                    |                               |
                                                     |                    |                               |
                                                     |                    |                               |
                                                     v                    v                               v
                                               onBeforeInstall      onInstallServer              onCompleteInstallation


.. list-table::
   :widths: 10 10 40
   :header-rows: 1

   * - Method
     - Arguments
     - Description

   * - **install**
     - ``serverGroup``
     - Entry point of the installation workflow.
       Iterates through all the servers of the passed ServerGroup and calls the
       ``checkServerIsInstalled`` method for each of them. If at least one
       of the calls has returned `false`, calls a ``beforeInstall`` method.
       Then, for each server which returned `false` as the result of the
       ``checkServerIsInstalled`` calls the ``installServer`` method to do
       the actual software installation.
       After the installation is completed on all the servers and if at
       least one of the previous calls of ``checkServerIsInstalled`` returned
       `false`, the method runs the ``completeInstallation`` method.
       If all the calls to ``checkServerIsInstalled`` return `true`, this
       method concludes without calling any others.

   * - **checkServerIsInstalled**
     - ``server``
     - Checks if the given server requires a (re)deployment of the software
       component. By default checks for the value of the attribute `installed`
       of the instance.
       May be overridden by subclasses to provide some better logic (e.g. the
       app developer may provide code to check if the given software is
       pre-installed on the image which was provisioned on the VM).

   * - **beforeInstall**
     - ``servers``, ``serverGroup``
     - Reports the beginning of installation process, sends notification about
       this event to all objects which are subscribed for it (see
       *Event notification pattern* section for details) and calls the public
       event handler ``onBeforeInstall``.

   * - **onBeforeInstall**
     - ``servers``, ``serverGroup``
     - Public handler of the `beforeInstall` event. Empty in the base class,
       may be overridden in subclasses if some custom pre-install logic needs
       to be executed.

   * - **installServer**
     - ``server``, ``serverGroup``
     - Does the actual software deployment on a given server by calling an
       ``onInstallServer`` public event handler (with notification on this
       event). If the installation completes successfully sets the `installed`
       attribute of the server to `true`, reports successful installation and
       returns `null`. If an exception encountered during the invocation of
       ``onInstallServer``, the method handles that exception, reports a
       warning and returns the server. The return value of the method indicates
       to the ``install`` method how many failures encountered in total during
       the installation and with what servers.

   * - **onInstallServer**
     - ``server``, ``serverGroup``
     - An event-handler method which is called by the ``installServer`` method
       when the actual software deployment is needed.It is empty in the base
       class. The implementations should override it with custom logic to
       deploy the actual software bits.

   * - **completeInstallation**
     - ``servers``, ``serverGroup``, ``failedServers``
     - It is executed after all the ``installServer`` methods were called.
       Checks for the number of errors reported during the installation: if it
       is greater than the value of ``allowedInstallFailures`` property, an
       exception is raised to interrupt the deployment workflow. Otherwise the
       method emits notification on this event, calls an
       ``onCompleteInstallation`` event handler and then reports the successful
       completion of the installation workflow.

   * - **onCompleteInstallation**
     - ``servers``, ``serverGroup``, ``failedServers``
     - An event-handler method which is called by the ``completeInstallation``
       method when the component installation is about to be completed.
       Default implementation is empty. Inheritors may implement this method to
       add some final handling, reporting etc.


**Configuration** workflow consists of the following methods:

::

 +----------------------------------------------------------------------------------------------------------------------+
 | CONFIGURATION                                                                                                        |
 |               +-----------------+                                                                                    |
 |               |                 |                                                                                    |
 |               |          +---------------+                          +-----------------+                              |
 |               |        +---------------+ |                        +-----------------+ |                              |
 |  +------------v--+   +---------------+ | |   +--------------+   +-----------------+ | |   +-----------------------+  |
 |  |               |   |               | | |   |              |   |                 | | |   |                       |  |
 |  | checkCluster\ +---> checkServer\  | +-+---> preConfigure +---> configureServer | +-+---> completeConfiguration |  |
 |  | IsConfigured  |   | IsConfigured  +-+     |              |   |                 +-+     |                       |  |
 |  +------------+--+   +---------------+       +------+-------+   +--------+--------+       +-----------+-----------+  |
 |               |                                     |                    |                            |              |
 |               |                                     |                    |                            |              |
 |    +----------v----------+                          |                    |                            |              |
 |    |                     |                          |                    |                            |              |
 |    | getConfigurationKey |                          |                    |                            |              |
 |    |                     |                          |                    |                            |              |
 |    +---------------------+                          |                    |                            |              |
 |                                                     |                    |                            |              |
 +----------------------------------------------------------------------------------------------------------------------+
                                                       |                    |                            |
                                                       |                    |                            |
                                                       v                    v                            v
                                               configureSecurity,    onConfigureServer          onCompleteConfiguration
                                                 onPreConfigure


.. list-table::
   :widths: 10 10 40
   :header-rows: 1

   * - Method
     - Arguments
     - Description

   * - **configure**
     - ``serverGroup``
     - Entry point of the configuration workflow.
       Calls a ``checkClusterIsConfigured`` method. If the call returns `true`,
       workflow exits without any further action. Otherwise for each server in
       the ``serverGroup`` it calls ``checkServerIsConfigured`` method and gets
       the list of servers that need reconfiguration. The ``preConfigure``
       method is called with that list. At the end calls the
       ``completeConfiguration`` method.

   * - **checkClusterIsConfigured**
     - ``serverGroup``
     - Has to return `true` if the configuration (i.e. the values of input
       properties) of the component has not been changed since it was last
       deployed on the given server group. Default implementation calls the
       ``getConfigurationKey`` method and compares the returned result with a
       value of `configuration` attribute of ``serverGroup``. If the results
       match returns `true` otherwise `false`.

   * - **getConfigurationKey**
     - None
     - Should return some values describing the configuration state of the
       component. This state is used to track the changes of the configuration
       by the ``checkClusterIsConfigured`` and ``checkServerIsConfigured``
       methods.
       Default implementation returns a synthetic value which gets updated on
       every environment redeployment. Thus the subsequent calls of the
       ``configure`` method on the same server group during the same deployment
       will not cause the reconfiguration, while the calls on the next
       deployment will reapply the configuration again.
       The inheritors may redefine this to include the actual values of the
       configuration properties, so the configuration is reapplied only if the
       appropriate input properties are changed.

   * - **checkServerIsConfigured**
     - ``server``, ``serverGroup``
     - It is called to check if the particular server of the server group has
       to be reconfigured thus providing more precise control compared to
       cluster-wide ``checkClusterIsConfigured``.
       Default implementation calls the ``getConfigurationKey`` method and
       compares the returned result with a value of `configuration` attribute
       of the server. If the results match returns `true` otherwise `false`.
       This method gets called only if the ``checkClusterIsConfigured`` method
       returned `false` for the whole server group.

   * - **preConfigure**
     - ``servers``, ``serverGroup``
     - Reports the beginning of configuration process, calls the
       ``configureSecurity`` method, emits the notification and calls the
       public event handler ``onPreConfigure``. This method is called once per
       the server group and only if the changes in configuration are detected.

   * - **configureSecurity**
     - ``servers``, ``serverGroup``
     - Intended for configuring the security rules. It is empty in the base
       class. Fully implemented in the ``OpenStackSecurityConfigurable`` class
       which is the inheritor of ``Configurable``.

   * - **onPreConfigure**
     - ``servers``, ``serverGroup``
     - Public event-handler which is called by the ``preConfigure`` method
       when the (re)configuration of the component is required.
       Default implementation is empty. Inheritors may implement this method to
       set various kinds of cluster-wide states or output properties which may
       be of use at later stages of the workflow.

   * - **configureServer**
     - ``server``, ``serverGroup``
     - Does the actual software configuration on a given server by calling the
       ``onConfigureServer`` public event handler. Before that reports the
       beginning of the configuration and emits the notification. If the
       configuration completes successfully calls the ``getConfigurationKey``
       method and sets the `configuration` attribute of the server to resulting
       value thus saving the configuration applied to a given server. Returns
       `null` to indicate successful configuration.
       If an exception encountered during the invocation of
       ``onConfigureServer``, the method will handle that exception, report a
       warning and return the current server to signal its failure to the
       ``configure`` method.

   * - **onConfigureServer**
     - ``server``, ``serverGroup``
     - An event-handler method which is called by the ``configureServer``
       method when the actual software configuration is needed. It is empty in
       the base class. The implementations should override it with custom logic
       to apply the actual software configuration on a given server.

   * - **completeConfiguration**
     - ``servers``, ``serverGroup``, ``failedServers``
     - It is executed after all the ``configureServer`` methods were called.
       Checks for the number of errors reported during the configuration: if it
       is greater than set by the ``allowedConfigurationFailures`` property, an
       exception is raised to interrupt the deployment workflow. Otherwise the
       method emits notification, calls an ``onCompleteConfiguration`` event
       handler, calls the ``getConfigurationKey`` method and sets the
       `configuration` attribute of the server group to resulting value and
       then reports successful completion of the configuration workflow.

   * - **onCompleteConfiguration**
     - ``servers``, ``serverGroup``, ``failedServers``
     - The event-handler method which is called by the ``completeConfiguration``
       method when the component configuration is finished at all the servers.
       Default implementation is empty. Inheritors may implement this method to
       add some final handling, reporting etc.


The ``OpenStackSecurityConfigurable`` class extends ``Configurable`` by
implementing the ``configureSecurity`` method of the base class and adding the
empty ``getSecurityRules`` method.

.. list-table::
   :widths: 10 10 40
   :header-rows: 1

   * - Method
     - Arguments
     - Description

   * - **getSecurityRules**
     - None
     - Returns an empty dictionary in default implementation. Inheritors which
       want to add security rules during the app configuration should
       implement this method and make it return a list of dictionaries
       describing the security rules with the following keys:

         * FromPort (port number, e.g. 80).

         * ToPort (port number, e.g. 80).

         * IpProtocol: (string, e.g. 'tcp').

         * External: (boolean: `true` means that the inbound traffic to the given
           port (or port range) may originate from outside of the environment;
           `false` means that only the VMs spawned by this or other apps of the
           current environment may connect to this port).

         * Ethertype: (optional, can be 'IPv4' or 'IPv6').

   * - **configureSecurity**
     - ``servers``, ``serverGroup``
     - Gets the list of security rules provided by the ``getSecurityRules``
       method and adds security group with these rules to the Heat stacks of
       all regions which the component's ``servers`` are deployed to

Consider the following example of this class usage:

.. code-block:: yaml

   Namespaces:
     =: com.example.apache
     apps: io.murano.applications

   Name: ApacheHttpServer

   Extends:
     - apps:MultiServerApplicationWithScaling
     - apps:OpenStackSecurityConfigurable

   Methods:
     getSecurityRules:
       Body:
         - Return:
             - ToPort: 80
               FromPort: 80
               IpProtocol: tcp
               External: true
             - ToPort: 443
               FromPort: 443
               IpProtocol: tcp
               External: true


In the example above, the ``ApacheHttpServer`` class is configured to create
a security group with two security rules allowing network traffic over HTTP
and HTTPS protocols on its deployment.


The ``SoftwareComponent`` class inherits both ``Installable`` and
``Configurable`` and adds several additional methods.

.. list-table::
   :widths: 10 10 40
   :header-rows: 1

   * - Method
     - Arguments
     - Description

   * - **deployAt**
     - ``serverGroup``
     - Binds all workflows into one process. Consequentially calls ``deploy``
       method of the ``serverGroup``, ``install`` and ``configure`` methods
       inherited from the parent classes.

   * - **report**
     - ``message``
     - Reports a ``message`` using environment's reporter.

   * - **detectSuccess**
     - ``allowedFailures``, ``serverGroup``, ``failedServers``
     - Static method that returns `true` in case the actual number of failures
       (number of ``failedServers``) is less than or equal to the
       ``allowedFailures``. The latter can be on of the following options:
       `none`, `one`, `two`, `three`, `any`, 'quorum'. `any` allows any number
       of failures during the installation or configuration. `quorum` allows
       failure of less than a half of all servers.


Event notification pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Event`` class may be used to issue various notifications to other
MuranoPL classes in an event-driven manner.

Any object which is going to emit the notifications should declare the
instances of the ``Event`` class as its public Runtime properties. You can see
the examples of such properties in the ``Installable`` and ``Configurable``
classes:

.. code-block:: yaml

   Name: Installable

   Properties:
     beforeInstallEvent:
       Contract: $.class(Event).notNull()
       Usage: Runtime
       Default:
         name: beforeInstall


The object which is going to subscribe for the notifications should pass
itself into the ``subscribe`` method of the event along with the name of its
method which will be used to handle the notification:

.. code-block:: yaml

   $event.subscribe($subscriber, handleFoo)


The specified handler method must be present in the subscriber class
(if the method name is missing it will default to ``handle%Eventname%``)
and have at least one standard (i.e. not ``VarArgs`` or ``KwArgs``) argument
which will be treated as ``sender`` while invoking.

The ``unsubscribe`` method does the opposite and removes object from the
subscribers of the event.

The class which is going to emit the notification should call the ``notify``
method of the event and pass itself as the first argument (``sender``). All
the optional parameters of the event may be passed as varargs/kwargs of the
``notify`` call. They will be passed all the way to the handler methods.

This is how it looks in the ``Installable`` class:

.. code-block:: yaml

   beforeInstall:
     Arguments:
       - servers:
           Contract:
             - $.class(res:Instance).notNull()
       - serverGroup:
           Contract: $.class(ServerGroup).notNull()
     Body:
       - ...
       - $this.beforeInstallEvent.notify($this, $servers, $serverGroup)
       - ...


The ``notifyInParallel`` method does the same, but invokes all handlers of
subscribers in parallel.


Base application classes
~~~~~~~~~~~~~~~~~~~~~~~~

There are several base classes that extend standard ``io.murano.Application``
class and ``SoftwareComponent`` class from the application development
library.

**SingleServerApplication**
    A base class for applications running a single software component on a
    single server only. Its ``deploy`` method simply creates the
    ``SingleServerGroup`` with the ``server`` provided as an application input.

**MultiServerApplication**
    A base class for applications running a single software component on
    multiple servers. Unlike ``SingleServerApplication``, it has the
    ``servers`` input property instead of ``server``. It accepts instance of
    on of the inheritors of the ``ServerGroup`` class.

**MultiServerApplicationWithScaling**
    Extends ``MultiServerApplication`` with the ability to scale the
    application by increasing (scaling out) or decreasing (scaling in) the
    number of nodes with the application after it is installed. The
    differences from ``MultiServerApplication`` are:

      * the ``servers`` property accepts only instances of
        ``ServerReplicationGroup`` rather than any ``ServerGroup``

      * the additional optional ``scaleFactor`` property accepts the number by
        which the app is scaled at once; it defaults to 1

      * the ``scaleOut`` and ``scaleIn`` public methods are added


Application developers may as well define their own classes using the
same approach and combining base classes behaviour with the custom code to
satisfy the needs of their applications.
