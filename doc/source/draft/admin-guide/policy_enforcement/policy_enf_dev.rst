.. _policyenf_dev:

Murano policy enforcement internals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes internals of the murano policy enforcement
feature.

Model decomposition
-------------------

The data for the policy validation comes from the models of Murano
applications. These models are transformed to a set of rules that are
processed by Congress.

There are several *tables* created in murano policy for different kinds
of rules that are as follows:

* ``murano:objects(object_id, parent_id, type_name)``
* ``murano:properties(object_id, property_name, property_value)``
* ``murano:relationships(source, target, name)``
* ``murano:connected(source, target)``
* ``murano:parent_types(object_id, parent_type_name)``
* ``murano:states(environment_id, state)``

**murano:objects(object_id, parent_id, type_name)**

  This rule is used for representation of all objects in Murano model,
  such as environment, application, instance, and other.

  Value of the ``type`` property is used as the ``type_name`` parameter:

  .. code-block:: yaml

      name: wordpress-env
      '?': {type: io.murano.Environment, id: 83bff5ac}
      applications:
      - '?': {id: e7a13d3c, type: com.example.databases.MySql}

  The model above transforms to the following rules:

  * ``murano:objects+("83bff5ac", "tenant_id", "io.murano.Environment")``
  * ``murano:objects+("83bff5ac", "e7a13d3c", "com.example.databases.MySql")``

  .. note::

     The owner of the environment is a project (tenant).

**murano:properties(object_id, property_name, property_value)**

  Each object may have properties. In this example we have an application
  with one property:

  .. code-block:: yaml

      applications:
      - '?': {id: e7a13d3c, type: com.example.databases.MySql}
      database: wordpress

  The model above transforms to the following rule:

  * ``murano:properties+("e7a13d3c", "database", "wordpress")``

  Inner properties are also supported using dot notation:

  .. code-block:: yaml

      instance:
      '?': {id: 825dc61d, type: io.murano.resources.LinuxMuranoInstance}
      networks:
        useFlatNetwork: false

  The model above transforms to the following rule:

  * ``murano:properties+("825dc61d", "networks.useFlatNetwork", "False")``

  If a model contains list of values, it is represented as a set of multiple
  rules:

  .. code-block:: yaml

     instances:
      - '?': {id: be3c5155, type: io.murano.resources.LinuxMuranoInstance}
      networks:
        customNetworks: [10.0.1.0, 10.0.2.0]

  The model above transforms to the following rules:

  * ``murano:properties+("be3c5155", "networks.customNetworks", "10.0.1.0")``
  * ``murano:properties+("be3c5155", "networks.customNetworks", "10.0.2.0")``

**murano:relationships(source, target, name)**

  Murano application models may contain references to other applications.
  In this example, the WordPress application references MySQL in
  the ``database`` property:

  .. code-block:: yaml

      applications:
      - '?':
          id: 0aafd67e
          type: com.example.databases.MySql
      - '?':
          id: 50fa68ff
          type: com.example.WordPress
        database: 0aafd67e

  The model above transforms to the following rule:

  * ``murano:relationships+("50fa68ff", "0aafd67e", "database")``

  .. note::

     For the ``database`` property we do not create
     the ``murano:properties+`` rule.

  If we define an object within other object, they will have relationships
  between them:

  .. code-block:: yaml

      applications:
      - '?':
          id: 0aafd67e
          type: com.example.databases.MySql
        instance:
          '?': {id: ed8df2b0, type: io.murano.resources.LinuxMuranoInstance}

  The model above transforms to the following rule:

  * ``murano:relationships+("0aafd67e", "ed8df2b0", "instance")``

  There are special relationships of ``services`` from the environment
  to its applications: ``murano:relationships+("env_id", "app_id",
  "services")``

**murano:connected(source, target)**

  This table stores both direct and indirect connections between instances.
  It is derived from ``murano:relationships``:

  .. code-block:: yaml

      applications:
      - '?':
          id: 0aafd67e
          type: com.example.databases.MySql
        instance:
          '?': {id: ed8df2b0, type: io.murano.resources.LinuxMuranoInstance}
      - '?':
          id: 50fa68ff
          type: com.example.WordPress
        database: 0aafd67e

  The model above transforms to the following rules:

  * ``murano:connected+("50fa68ff", "0aafd67e")`` # WordPress to MySql
  * ``murano:connected+("50fa68ff", "ed8df2b0")`` # WordPress to LinuxMuranoInstance
  * ``murano:connected+("0aafd67e", "ed8df2b0")`` # MySql to LinuxMuranoInstance

**murano:parent_types(object_id, parent_name)**

  Each object in murano has a class type. These classes may inherit from one
  or more parents. For example, ``LinuxMuranoInstance > LinuxInstance >
  Instance``:

  .. code-block:: yaml

      instances:
      - '?': {id: be3c5155, type: LinuxMuranoInstance}

  The model above transforms to the following rules:

  * ``murano:objects+("...", "be3c5155", "LinuxMuranoInstance")``
  * ``murano:parent_types+("be3c5155", "LinuxMuranoInstance")``
  * ``murano:parent_types+("be3c5155", "LinuxInstance")``
  * ``murano:parent_types+("be3c5155", "Instance")``

  .. note::

     The type of an object is also repeated in its parent types
     (``LinuxMuranoInstance`` in the example) for easier handling of
     user-created rules.

  .. note::

     If a type inherits from more than one parent, and these parents inherit
     from one common type, the ``parent_type`` rule is included only once in
     the common type.

**murano:states(environment_id, state)**

  Currently only one record for environment is created:

  * ``murano:states+("uugi324", "pending")``

