Part 4: Refactoring code to use the Application Framework
---------------------------------------------------------

Up until this point we wrote the Plone application in a manner that was common
to all applications that were written before the application framework was
introduced.

In this last tutorial step we are going to refactor the Plone code in order
to take advantage of the framework.

Application framework was written in order to simplify the application
development and encapsulate common deployment workflows. This gives things
primitives for application scaling and high availability without the need to
develop them over and over again for each application.

When using the frameworks, an application developer only has to inherit the
class that best suits him and provide it only with the code that is specific
to the application, while leaving the rest to the framework.
This typically includes:

* instructions on how to provision the software on each node (server)
* instructions on how to configure the provisioned software
* server group onto which the software should be installed. This may be a
  fixed server list, a shared server pool, or a scalable server group that
  creates servers using the given instance template, or one of the several
  other implementations provided by the framework

The framework is located in a separate library package
``io.murano.applications`` that is shipped with Murano. We are going to use
the ``apps`` namespace prefix to refer to this namespace through the code.

Step 1: Add dependency on the App Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to use one Murano Package from another, the former must be explicitly
specified as a requirement for the latter. This is done by filling the
``Require`` section in the package's manifest file.

Open the Plone's manifest.yaml file and append the following lines:

.. code-block:: yaml

   Require:
     io.murano.applications:

Requirements are specified as a mapping from package name to the desired
version of that package (or version range). The missing value indicates
the dependency on the latest ``0.*.*`` version of the package which is exactly
what we need since the current version of the app framework library is 0.

Step 2: Get rid of the instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since we are going to have a multi-sever Plone application there won't be
a single instance belonging to the application. Instead, we are going to
provide it with the server group that abstracts the server management from
the application.

So instead of

.. code-block:: yaml

   Properties:
     instance:
       Contract: $.class(res:Instance)

we are going to have

.. code-block:: yaml

   Properties:
     servers:
       Contract: $.class(apps:ServerGroup).notNull()


Step 3: Change the base classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Another change that we are going to make to the main application class is
to change its base classes. Regular applications inherit from the
``std:Application`` which only has the method ``deploy`` that does all the
work.

Application framework provides us with its own implementation of that class and
method. Instead of one monolithic method that does everything, with the
framework, the application provides only the code needed to provision and
configure the software on each server.

So instead of ``std:Application`` class we are going to inherit two of
the framework classes:

.. code-block:: yaml

   Extends:
     - apps:MultiServerApplicationWithScaling
     - apps:OpenStackSecurityConfigurable

The first class tells us that we are going to have an application that runs
on multiple servers. In the following section we are going to split out
``deploy`` method into two smaller methods that are going to be invoked by
the framework to install the software on each of the servers. By inheriting the
``apps:MultiServerApplicationWithScaling``, the application automatically gets
all the UI buttons to scale it out and in.

The second class is a mix-in class that tells the framework that we are going
to provide the OpenStack-specific security group configuration for the
application.


Step 4: Split the deployment logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this step we are going to split the installation into two phases:
provisioning and configuration.

Provisioning is implemented by overriding the ``onInstallServer`` method,
which is called every time a new server is added to the server group. In this
method we are going to install the Plone software bits onto the server
(which is provided as a method parameter).

Configuration is done through the ``onConfigureServer``, which is called
upon the first installation on the server, and every time any of the
application settings change, and ``onCompleteConfiguration`` which is
executed on each server after everything was configured so that we can
perform post-configuration steps like starting application daemons and
reporting messages to the user.

Thus we are going to split the ``install-plone.sh`` script into two scripts:
``installPlone.sh`` and ``configureServer.sh`` and execute each one in their
corresponding methods:

.. code-block:: yaml

   onInstallServer:
     Arguments:
       - server:
           Contract: $.class(res:Instance).notNull()
       - serverGroup:
           Contract: $.class(apps:ServerGroup).notNull()
     Body:
       - $file: sys:Resources.string('installPlone.sh').replace({
             "$1" => $this.deploymentPath,
             "$2" => $this.adminPassword
           })
       - conf:Linux.runCommand($server.agent, $file)

   onConfigureServer:
     Arguments:
       - server:
           Contract: $.class(res:Instance).notNull()
       - serverGroup:
           Contract: $.class(apps:ServerGroup).notNull()
     Body:
       - $primaryServer: $serverGroup.getServers().first()
       - If: $server = $primaryServer
         Then:
           - $file: sys:Resources.string('configureServer.sh').replace({
                 "$1" => $this.deploymentPath,
                 "$2" => $primaryServer.ipAddresses[0]
               })
         Else:
           - $file: sys:Resources.string('configureClient.sh').replace({
               "$1" => $this.deploymentPath,
               "$2" => $this.servers.primaryServer.ipAddresses[0],
               "$3" => $this.listeningPort})
       - conf:Linux.runCommand($server.agent, $file)


     onCompleteConfiguration:
       Arguments:
         - servers:
             Contract:
               - $.class(res:Instance).notNull()
         - serverGroup:
             Contract: $.class(apps:ServerGroup).notNull()
         - failedServers:
             Contract:
               - $.class(res:Instance).notNull()
       Body:
         - $startCommand: format('{0}/zeocluster/bin/plonectl start', $this.deploymentPath)
         - $primaryServer: $serverGroup.getServers().first()
         - If: $primaryServer in $servers
           Then:
             - $this.report('Starting DB node')
             - conf:Linux.runCommand($primaryServer.agent, $startCommand)
             - conf:Linux.runCommand($primaryServer.agent, 'sleep 10')

         - $otherServers: $servers.where($ != $primaryServer)
         - If: $otherServers.any()
           Then:
             - $this.report('Starting Client nodes')
             # run command on all other nodes in parallel with pselect
             - $otherServers.pselect(conf:Linux.runCommand($.agent, $startCommand))

         # build an address string with IPs of all our servers
         - $addresses: $serverGroup.getServers().
             select(
               switch($.assignFloatingIp => $.floatingIpAddress,
                      true => $.ipAddresses[0])
               + ':' + str($this.listeningPort)
             ).join(', ')
         - $this.report('Plone listeners are running at ' + str($addresses))

During configuration phase we distinguish the first server in the server group
from the rest of the servers. The first server is going to be the primary
node and treated differently from the others.

Step 5: Configuring OpenStack security group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The last change to the main class is to set up the security group rules.
We are going to do this by overriding the ``getSecurityRules`` method
that we inherited from the ``apps:OpenStackSecurityConfigurable`` class:

.. code-block:: yaml

   getSecurityRules:
     Body:
       - Return:
           - FromPort: $this.listeningPort
             ToPort: $this.listeningPort
             IpProtocol: tcp
             External: true
           - FromPort: 8100
             ToPort: 8100
             IpProtocol: tcp
             External: false

The code is very similar to that of the old ``deploy`` method with the only
difference being that it returns the rules rather than sets them on its own.

Step 6: Provide the server group instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Do you remember, that previously we replaced the ``instance`` property with
``servers`` of type ``apps:ServerGroup``? Since the object is coming from the
UI definition, we must change the latter in order to provide
the class with the ``apps:ServerReplicationGroup`` instance rather than
``resources:Instance``.

To do this we are going to replace the ``instance`` property in the
Application template with the following snippet:

.. code-block:: yaml

   servers:
     ?:
       type: io.murano.applications.ServerReplicationGroup
     numItems: $.ploneConfiguration.numNodes
     provider:
       ?:
         type: io.murano.applications.TemplateServerProvider
       template:
         ?:
           type: io.murano.resources.LinuxMuranoInstance
         flavor: $.instanceConfiguration.flavor
         image: $.instanceConfiguration.osImage
         assignFloatingIp: $.instanceConfiguration.assignFloatingIP
       serverNamePattern: $.instanceConfiguration.unitNamingPattern

If you take a closer look at the code above you will find out that the
new declaration is very similar to the old one. But now instead of providing
the ``Instance`` property values directly, we are providing them as a template
for the ``TemplateServerProvider`` server provider. ``ServerReplicationGroup``
is going to use the provider each time it requires another server. In turn,
the provider is going to use the familiar template for the new instances.

Besides the instance template we also specify the initial number of Plone
nodes using the ``numItems`` property and the name pattern for the servers.
Thus we must also add it to the list of our controls:

.. code-block:: yaml

   Forms:
     - instanceConfiguration:
         fields:
           ...
           - name: unitNamingPattern
             type: string
             label: Instance Naming Pattern
             required: false
             maxLength: 64
             initial: 'plone-{0}'
             description: >-
               Specify a string, that will be used in instance hostname.
               Just A-Z, a-z, 0-9, dash and underline are allowed.

     - ploneConfiguration:
         fields:
           ...
           - name: numNodes
             type: integer
             label: Initial number of Client Nodes
             initial: 1
             minValue: 1
             required: true
             description: >-
               Select the initial number of Plone Client Nodes

Step 6: Using server group composition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By this step we should already have a working Plone application. But let's
go one step further and enhance our sample application.

Since we are running the database on the first server group server only,
we might want it to have different properties. For example we might want
to give it a bigger flavor or just a special name. This is a perfect
opportunity for us to demonstrate how to construct complex server groups.
All we need to do is to just use another implementation of
``apps:ServerGroup``. Instead of ``apps:ServerReplicationGroup`` we are going
to use the ``apps:CompositeServerGroup`` class, which allows us to compose
several server groups together. One of them is going to be a single-server
server group consisting of our primary server, and the second is going to be
the scalable server group that we used to create in the previous step.

So again, we change the ``Application`` section of our UI definition file
with even a more advanced ``servers`` property definition:

.. code-block:: yaml

   servers:
     ?:
       type: io.murano.applications.CompositeServerGroup
     serverGroups:
       - ?:
           type: io.murano.applications.SingleServerGroup
         server:
           ?:
             type: io.murano.resources.LinuxMuranoInstance
           name: format($.instanceConfiguration.unitNamingPattern, 'db')
           image: $.instanceConfiguration.image
           flavor: $.instanceConfiguration.flavor
           assignFloatingIp: $.instanceConfiguration.assignFloatingIp
       - ?:
           type: io.murano.applications.ServerReplicationGroup
         numItems: $.ploneConfiguration.numNodes
         provider:
           ?:
             type: io.murano.applications.TemplateServerProvider
           template:
             ?:
               type: io.murano.resources.LinuxMuranoInstance
             flavor: $.instanceConfiguration.flavor
             image: $.instanceConfiguration.osImage
             assignFloatingIp: $.instanceConfiguration.assignFloatingIP
           serverNamePattern: $.instanceConfiguration.unitNamingPattern

Here the instance definition for the ``SingleServerGroup`` (our primary
server) differs from the servers in the ``ServerReplicationGroup`` by its name
only. However the same technique might be used to customize other properties
as well as to create even more sophisticated server group topologies. For
example, we could implement region bursting by composing several scalable
server groups that allocate servers in different regions. And all of that
without making any changes to the application code itself!
