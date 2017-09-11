.. _core_lib:

MuranoPL Core Library
~~~~~~~~~~~~~~~~~~~~~

Some objects and actions can be used in several application deployments.
All common parts are grouped into MuranoPL libraries.
Murano core library is a set of classes needed in each deployment.
Class names from core library can be used in the application definitions.
This library is located under the `meta <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano>`_
directory.

Classes included in the Murano core library are as follows:

**io.murano**

- :ref:`object`
- :ref:`application`
- :ref:`security-group-manager`
- :ref:`environment`
- :ref:`cloud-region`

**io.murano.resources**

- :ref:`instance`
- :ref:`network`

**io.murano.system**

- :ref:`logger`
- :ref:`status-reporter`


.. _object:

Class: Object
-------------

A parent class for all MuranoPL classes. It implements the ``initialize``,
``setAttr``, and ``getAttr`` methods defined in the pythonic part of the Object class.
All MuranoPL classes are implicitly inherited from this class.

.. seealso::

   Source `Object.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/Object.yaml>`_
   file.



.. _application:

Class: Application
------------------

Defines an application itself. All custom applications must be derived from
this class.

.. seealso::

   Source `Application.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/Application.yaml>`_
   file.


.. _security-group-manager:

Class: SecurityGroupManager
---------------------------

Manages security groups during an application deployment.

.. seealso::

   Source `SecurityGroupManager.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/system/SecurityGroupManager.yaml>`_
   file.


.. _cloud-region:

Class: CloudRegion
------------------

Defines a CloudRegion and groups region-local properties

.. list-table:: **CloudRegion class properties**
   :widths: 10 35 7
   :header-rows: 1

   * - Property
     - Description
     - Default usage
   * - ``name``
     - A region name.
     - ``In``
   * - ``agentListener``
     - A property containing the ``io.murano.system.AgentListener`` object
       that can be used to interact with Murano Agent.
     - ``Runtime``
   * - ``stack``
     - A property containing a HeatStack object that can be used to interact
       with Heat.
     - ``Runtime``
   * - ``defaultNetworks``
     - A property containing user-defined Networks
       (``io.murano.resources.Network``) that can be used as default networks
       for the instances in this environment.
     - ``In``
   * - ``securityGroupManager``
     - A property containing the ``SecurityGroupManager`` object that can
       be used to construct a security group associated with this environment.
     - ``Runtime``


.. seealso::

   Source `CloudRegion.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/CloudRegion.yaml>`_
   file.

.. _environment:

Class: Environment
------------------

Defines an environment in terms of the deployment process and
groups all Applications and their related infrastructures. It also able
to deploy them at once.

Environments is intent to group applications to manage them easily.

.. list-table:: **Environment class properties**
   :widths: 10 35 7
   :header-rows: 1

   * - Property
     - Description
     - Default usage
   * - ``name``
     - An environment name.
     - ``In``
   * - ``applications``
     - A list of applications belonging to an environment.
     - ``In``
   * - ``agentListener``
     - A property containing the ``io.murano.system.AgentListener`` object
       that can be used to interact with Murano Agent.
     - ``Runtime``
   * - ``stack``
     - A property containing a HeatStack object in default region that can
       be used to interact with Heat.
     - ``Runtime``
   * - ``instanceNotifier``
     - A property containing the ``io.murano.system.InstanceNotifier`` object
       that can be used to keep track of the amount of deployed instances.
     - ``Runtime``
   * - ``defaultNetworks``
     - A property containing templates for user-defined Networks in regions
       (``io.murano.resources.Network``).
     - ``In``
   * - ``securityGroupManager``
     - A property containing the ``SecurityGroupManager`` object from default region
       that can be used to construct a security group associated with this environment.
     - ``Runtime``
   * - ``homeRegionName``
     - A property containing the name of home region from `murano` config
     - ``Runtime``
   * - ``regions``
     - A property containing the map `regionName` -> `CloudRegion` instance.
     - ``InOut``
   * - ``regionConfigs``
     - A property containing the map `regionName` -> `CloudRegion` config
     - ``Config``

.. seealso::

   Source `Environment.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/Environment.yaml>`_
   file.


.. _instance:

Class: Instance
---------------

Defines virtual machine parameters and manages an instance lifecycle: spawning,
deploying, joining to the network, applying security group, and deleting.

.. list-table:: **Instance class properties**
   :widths: 10 35 7
   :header-rows: 1

   * - Property
     - Description
     - Default usage
   * - ``regionName``
     - Inherited from ``CloudResource``. Describe region for instance deployment
     - ``In``
   * - ``name``
     - An instance name.
     - ``In``
   * - ``flavor``
     - An instance flavor defining virtual machine hardware parameters.
     - ``In``
   * - ``image``
     - An instance image defining operation system.
     - ``In``
   * - ``keyname``
     - Optional. A key pair name used to connect easily to the instance.
     - ``In``
   * - ``agent``
     - Configures interaction with the Murano agent using
       ``io.murano.system.Agent``.
     - ``Runtime``
   * - ``ipAddresses``
     - A list of all IP addresses assigned to an instance. Floating ip address
       is placed in the list tail if present.
     - ``Out``
   * - ``networks``
     - Specifies the networks that an instance will be joined to.
       Custom networks that extend :ref:`Network class <Network>` can be
       specified. An instance will be connected to them and for the default
       environment network or flat network if corresponding values are set
       to ``True``. Without additional configuration, instance will be joined
       to the default network that is set in the current environment.
     - ``In``
   * - ``volumes``
     - Specifies the mapping of a mounting path to volume implementations
       that must be attached to the instance. Custom volumes that extend
       ``Volume`` class can be specified.
     - ``In``
   * - ``blockDevices``
     - Specifies the list of block device mappings that an instance will use
       to boot from. Each mapping defines a volume that must be an instance of
       ``Volume`` class, device name, device type, and boot order.
       Either the ``blockDevices`` property or ``image`` property must be
       specified in order to boot an instance
     - ``In``
   * - ``assignFloatingIp``
     - Determines if floating IP is required. Default is ``False``.
     - ``In``
   * - ``floatingIpAddress``
     - IP addresses assigned to an instance after an application deployment.
     - ``Out``
   * - ``securityGroupName``
     - Optional. A security group that an instance will be joined to.
     - ``In``

.. seealso::

   Source `Instance.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/resources/Instance.yaml>`_
   file.


.. _instance-resources:

Resources
+++++++++

Instance class uses the following resources:

**Agent-v2.template**
 Python Murano Agent template.

 .. note::

    This agent is supposed to be unified. Currently, only Linux-based
    machines are supported. Windows support will be added later.

**linux-init.sh**
 Python Murano Agent initialization script that sets up an agent with
 valid information containing an updated agent template.

**Agent-v1.template**
 Windows Murano Agent template.

**windows-init.sh**
 Windows Murano Agent initialization script.


.. _network:

Class: Network
--------------

The basic abstract class for all MuranoPL classes representing networks.

.. seealso::

   Source `Network.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/resources/Network.yaml>`_
   file.

.. _logger:

Class: Logger
-------------

Logging API is the part of core library since Liberty release. It was
introduced to improve debuggability of MuranoPL programs.

You can get a logger instance by calling a ``logger`` function which
is located in  ``io.murano.system`` namespace. The ``logger`` function takes
a logger name as the only parameter. It is a common recommendation to use full
class name as a logger name within that class. This convention avoids names
conflicts in logs and ensures a better logging subsystem configurability.

Logger class instantiation:

.. code-block:: yaml

    $log: logger('io.murano.apps.activeDirectory.ActiveDirectory')


.. list-table:: **Log levels prioritized in order of severity**
   :widths: 10 35
   :header-rows: 1

   * - Level
     - Description
   * - CRITICAL
     - Very severe error events that will presumably lead the application
       to abort.
   * - ERROR
     - Error events that might not prevent the application from running.
   * - WARNING
     - Events that are potentially harmful but will allow the application
       to continue running.
   * - INFO
     - Informational messages highlighting the progress of the application
       at the coarse-grained level.
   * - DEBUG
     - Detailed informational events that are useful when debugging an
       application.
   * - TRACE
     - Even more detailed informational events comparing to the DEBUG level.

There are several methods that fully correspond to the log levels you can use
for logging events. They are ``debug``, ``trace``, ``info``, ``warning``,
``error``, and ``critical``.

Logging example:

.. code-block:: yaml

  $log.info('print my info message {message}', message=>message)

Logging methods use the same format rules as the YAQL :command:`format`
function. Thus the line above is equal to the:

.. code-block:: yaml

   $log.info('print my info message {message}'.format(message=>message))

To print an exception stacktrace, use the :command:`exception` method.
This method uses the ERROR level:

.. code-block:: yaml

   Try:
     - Throw: exceptionName
       Message: exception message
   Catch:
   With: exceptionName
   As: e
   Do:
     - $log.exception($e, 'something bad happen "{message}"', message=>message)

.. note::
    You can configure the logging subsystem through the ``logging.conf`` file
    of the Murano Engine.

.. seealso::

  * Source `Logger.yaml
    <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/system/Logger.yaml>`_
    file.

  * `OpenStack networking logging
    configuration <https://docs.openstack.org/liberty/config-reference/content/networking-options-logging.html>`_.

.. _status-reporter:

Class: StatusReporter
---------------------

Provides feedback feature. To follow the deployment process in the UI, all status changes should be included
in the application configuration.

.. seealso::

   Source `StatusReporter.yaml
   <https://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Classes/system/StatusReporter.yaml>`_
   file.
