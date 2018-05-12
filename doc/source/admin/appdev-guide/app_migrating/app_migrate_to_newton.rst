.. _app_migrate_to_newton:

Migrate applications to Stable/Newton
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Newton a number of useful features that can be used by developers creating
their murano applications were implemented. Also some changes are not backward
compatible. This document describes these features, how they may be included
into the new apps and what benefits the apps may gain.


1. New syntax for the action declaration
----------------------------------------

Previously, for declaring action in MuranoPL application, following syntax was
used:

  .. code-block:: yaml

    methodName:
      Usage: Action

This syntax is deprecated now for packages with FormatVersion starting from
1.4, and you should use the `Scope` attribute:

  .. code-block:: yaml

    methodName:
      Scope: Public

For more information about actions in MuranoPL, see :ref:`actions`.


2. Usage of static methods as Action
------------------------------------

Now you can declare static method as action with `Scope` and `Usage`
attributes

  .. code-block:: yaml

    methodName:
      Scope: Public
      Usage: Static

For more information about static methods in MuranoPL, see :ref:`static_methods_and_properties`.

3. Template contract support
----------------------------

New contract function ``template`` was introduced. ``template`` works
similar to the ``class`` in regards to the data validation but does not
instantiate objects. The template is just a dictionary with object model
representation of the object.

It is useful when you do not necessarily need to pass the actual object as a
property or as a method argument and use it right away, but rather to create
new objects of this type in runtime from the given template. It is especially
beneficial for resources replication or situations when object creation
depends on some conditions.

Objects that are assigned to the property or argument with ``template``
contract will be automatically converted to their object model
representation.

4. Multi-region support
-----------------------

Starting from Newton release cloud resource classes (instances, networks,
volumes) can be explicitly put into OpenStack regions other than environment
default. Thus it becomes possible to have applications that make use of more
than one region including stretching/bursting to other regions.

Each resource class has got new ``regionName`` property which controls its
placement. If no value is provided, default region for environment is used.
Applications wanting to take advantage of multi-region support should access
security manager and Heat stacks from regions of their resources rather than
from the environment.

Regions need to be configured before they can be used. Please refer to
documentation on how to do this: :ref:`multi_region`.

Changes in the core library
```````````````````````````

`io.murano.Environment` class contains `regions` property with list of
`io.murano.CloudRegion` objects. Heat stack, networks and agent listener are
now owned by `io.murano.CloudRegion` instances rather than by `Environment`.

You can not get `io.murano.resources.Network` objects from
`Enviromnent::defaultNetworks` now. This property only contains templates for
`io.murano.CloudRegion` default networks.

The proper way to retrieve `io.murano.resources.Network` object is now the
following:

    .. code-block:: yaml

        $region: $instance.getRegion()
        $networks: $region.defaultNetworks

5. Changes to property validation
---------------------------------

`string()` contract no longer converts to string anything but scalar values.

6. Garbage collection
---------------------

New approach to resource deallocation was introduced.

Previously murano used to load ``Objects`` and ``ObjectsCopy`` sections of the
JSON object model independently which cause for objects that were not deleted
between deployments to instantiate twice. If deleted objects were to cause any
changes to such alive objects they were made to the objects loaded from
``ObjectsCopy`` and immediately discarded before the deployment.
Now this behaviour is changed and there are no more duplicates of the same object.

Applications can also make use of the new features. Now it is possible to
perform on-demand destruction of the unreferenced MuranoPL objects during the
deployment from the application code.
The ``io.murano.system.GC.GarbageCollector.collect()`` static method may be
used for that.

Also objects obtained ability to set up destruction dependencies to the
other objects. Destruction dependencies allow to define the preferable order
of objects destruction and let objects be aware of other objects destruction,
react to this event, including the ability to prevent other objects from
being destroyed.

Please refer to the documentation on how to use the
:ref:`Garbage Collector <garbage_collection>`.
