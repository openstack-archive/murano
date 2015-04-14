===========================================
Murano Policy Enforcement - Developer Guide
===========================================

.. _policyenf_dev:

This document describes internals of murano policy enforcement.

Model Decomposition
-------------------

Models of Murano applications are transformed to set of rules that are processed by congress. This represent data for policy validation.

There are several "tables" created in murano policy for different kind of rules:

- ``murano:objects(object_id, parent_id, type_name)``
- ``murano:properties(object_id, property_name, property_value)``
- ``murano:relationships(source, target, name)``
- ``murano:connected(source, target)``
- ``murano:parent_types(object_id, parent_type_name)``
- ``murano:states(environment_id, state)``

``murano:objects(object_id, parent_id, type_name)``
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

This rule is used for representation of all objects in Murano model (environment, applications, instances, ...).
Value of property ``type`` is used as ``type_name`` parameter:

.. code-block:: yaml

    name: wordpress-env
    '?': {type: io.murano.Environment, id: 83bff5ac}
    applications:
    - '?': {id: e7a13d3c, type: io.murano.databases.MySql}
..

Transformed to these rules:

- ``murano:objects+("83bff5ac", "tenant_id", "io.murano.Environment")``
- ``murano:objects+("83bff5ac", "e7a13d3c", "io.murano.databases.MySql")``

.. note:: The owner of the environment is a tenant


``murano:properties(object_id, property_name, property_value)``
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Each object can have properties. In this example we have application with one property:

.. code-block:: yaml

    applications:
    - '?': {id: e7a13d3c, type: io.murano.databases.MySql}
    database: wordpress
..

Transformed to this rule:

- ``murano:properties+("e7a13d3c", "database", "wordpress")``

Inner properties are also supported using dot notation:

.. code-block:: yaml

    instance:
    '?': {id: 825dc61d, type: io.murano.resources.LinuxMuranoInstance}
    networks:
      useFlatNetwork: false
..

Transformed to this rule:

- ``murano:properties+("825dc61d", "networks.useFlatNetwork", "False")``

If model contains list of values it is represented as set of multiple rules:

.. code-block:: yaml

    instances:
    - '?': {id: be3c5155, type: io.murano.resources.LinuxMuranoInstance}
    networks:
      customNetworks: [10.0.1.0, 10.0.2.0]
..

Transformed to these rules:

- ``murano:properties+("be3c5155", "networks.customNetworks", "10.0.1.0")``
- ``murano:properties+("be3c5155", "networks.customNetworks", "10.0.2.0")``

``murano:relationships(source, target, name)``
""""""""""""""""""""""""""""""""""""""""""""""

Murano app models can contain references to other applications. In this example WordPress application references MySQL in property "database":

.. code-block:: yaml

    applications:
    - '?':
        id: 0aafd67e
        type: io.murano.databases.MySql
    - '?':
        id: 50fa68ff
        type: io.murano.apps.WordPress
      database: 0aafd67e
..

Transformed to this rule:

- ``murano:relationships+("50fa68ff", "0aafd67e", "database")``

.. note:: For property "database" we do not create rule ``murano:properties+``.

Also if we define inner object inside other object, they will have relationship between them:

.. code-block:: yaml

    applications:
    - '?':
        id: 0aafd67e
        type: io.murano.databases.MySql
      instance:
        '?': {id: ed8df2b0, type: io.murano.resources.LinuxMuranoInstance}
..

Transformed to this rule:

- ``murano:relationships+("0aafd67e", "ed8df2b0", "instance")``

There are special relationships "services" from the environment to its applications:

- ``murano:relationships+("env_id", "app_id", "services")``


``murano:connected(source, target)``
""""""""""""""""""""""""""""""""""""

This table stores both direct and indirect connections between instances. It is derived from the ``murano:relationships``:

.. code-block:: yaml

    applications:
    - '?':
        id: 0aafd67e
        type: io.murano.databases.MySql
      instance:
        '?': {id: ed8df2b0, type: io.murano.resources.LinuxMuranoInstance}
    - '?':
        id: 50fa68ff
        type: io.murano.apps.WordPress
      database: 0aafd67e
..

Transformed to rules:

- ``murano:connected+("50fa68ff", "0aafd67e")`` # WordPress to MySql
- ``murano:connected+("50fa68ff", "ed8df2b0")`` # WordPress to LinuxMuranoInstance
- ``murano:connected+("0aafd67e", "ed8df2b0")`` # MySql to LinuxMuranoInstance


``murano:parent_types(object_id, parent_name)``
"""""""""""""""""""""""""""""""""""""""""""""""

Each object in murano has class type and these classes can inherit from one or more parents:

e.g. ``LinuxMuranoInstance`` > ``LinuxInstance`` > ``Instance``

So this model:

.. code-block:: yaml

    instances:
    - '?': {id: be3c5155, type: LinuxMuranoInstance}
..

Transformed to these rules:

- ``murano:objects+("...", "be3c5155", "LinuxMuranoInstance")``
- ``murano:parent_types+("be3c5155", "LinuxMuranoInstance")``
- ``murano:parent_types+("be3c5155", "LinuxInstance")``
- ``murano:parent_types+("be3c5155", "Instance")``

.. note:: Type of object is also repeated among parent types (``LinuxMuranoInstance`` in example) for easier handling of user-created rules.

.. note:: If type inherits from more than one parent and those parents inherit from one common type, ``parent_type`` rule is included only once for common type.

``murano:states(environment_id, state)``
""""""""""""""""""""""""""""""""""""""""

Currently only one record for environment is created:

- ``murano:states+("uugi324", "pending")``