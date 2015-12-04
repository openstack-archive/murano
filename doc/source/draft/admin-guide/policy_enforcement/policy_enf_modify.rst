Using policy for the base modification of an environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Congress policies enables a user to define modification of an environment
prior to its deployment. This includes:

* Adding components, for example, monitoring.
* Changing and setting properties, for example enforcing a given zone,
  flavors, and others.
* Configuring relationships within an environment.

Use cases examples:

* Installation of the monitoring agent on each VM instance
  by adding a component with the agent and creating relationship
  between the agent and instance.

* Enabling a certified version to all Apache server instances:
  setting the version property to all Apache applications within
  an environment to a particular version.

These policies are evaluated over data in the form of tables that are Congress
data structures. A deployed murano environment must be decomposed to Congress
data structures. The further workflow is as follows:

* The decomposed environment is sent to Congress for simulation.

* Congress simulates whether the resulting state requires modification.

* In case the modification of a deployed environment is required,
  Congress returns a list of actions in the YAML format
  to be performed on the environment prior to the deployment.

  For example:

  .. code-block:: yaml

     set-property: {object_id: c46770dec1db483ca2322914b842e50f, prop_name: keyname, value: production-key}

  The example above sets the ``keyname`` property to the ``production-key``
  value on the instance identified by ``object_id``. An administrator can use
  it as an output of the Congress rules.

* The action specification is parsed in murano. The given action class is
  loaded, and the action instance is created.

* The parsed parameters are supplied to the action ``__init__`` method.

* The action is performed on a given environment (the ``modify`` method).


.. _base_mod_rules:

Creating base modification rules
--------------------------------

This example illustrates how to configure the rule enforcing all VM instances
to deploy with a secure key pair. This may be required in a production
environment.

.. warning::

   Before you create rules, configure your OpenStack environment as described
   in :ref:`policyenf_setup`.

**Procedure:**

#. To create the ``predeploy_modify`` rule, run:

   .. code-block:: console

      congress policy rule create murano_system 'predeploy_modify(eid, obj_id, action):-murano:objects(obj_id, pid, type), murano_env_of_object(obj_id, eid), murano:properties(obj_id, "keyname", kn), concat("set-property: {object_id: ", obj_id, first_part), concat(first_part, ", prop_name: keyname, value: production-key}", action)'

   The command above contains the following information:

   .. code-block:: console

      predeploy_modify(eid, obj_id, action) :-
         murano:objects(obj_id, pid, type),
         murano:objects(eid, tid, "io.murano.Environment"),
         murano:connected(eid, pid),
         murano:properties(obj_id, "keyname", kn),
         concat("set-property: {object_id: ", obj_id, first_part),
         concat(first_part, ", prop_name: keyname, value: production-key}", action)

   Policy validation engine checks the ``predeploy_modify`` rule.
   And the Congress engine evaluates the rules referenced inside this rule.

   .. note::

      The ``production-key`` key pair must already exist, though you can use
      any other existing key pair.

#. Deploy the environment.

Instances within the environment are deployed with the specified key pair.

.. seealso::

   * :ref:`policy_enf_rules`

