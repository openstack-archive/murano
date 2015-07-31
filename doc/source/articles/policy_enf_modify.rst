=======================================================
Murano Policy Based Modification of Environment Example
=======================================================

Introduction
============
Goal is to be able to define modification of an environment by Congress policies prior
deployment. This allows to add components (for example monitoring), change/set properties
(for example to enforce given zone, flavors, ...) and relationships into environment,
so modified environment is after that deployed.

Example Use Cases:

* install monitoring agent on each VM instance (adding component with the agent and creating relationship between
   agent and instance)
* all Apache server instances must have given certified version (version property is set on all Apache applications
   within environment to given version)

These policies are evaluated over data in the form of tables (Congress data structures). A deployed Murano environment must be
decomposed to Congress data structures. The decomposed environment is sent to congress for simulation. Congress simulates
whether the resulting state needs to be modified. In case that modifications of deployed environment are needed congress returns
list of actions which needs to be performed on given environment prior the deployment. Actions and its parameters are returned
from congress in YAML format.

Example of action specification returned from congress:

* set ``keyname`` property on instance identified by ``object_id`` to value ``production-key``

    .. code-block:: yaml

        set-property: {object_id: c46770dec1db483ca2322914b842e50f, prop_name: keyname, value: production-key}
    ..

Administrator can use above one line action specification as output of congress rules. This action specification
is parsed in murano. Given action class is loaded. Action instance is created. Parsed parameters are supplied to action
``__init__`` method. Then action is performed on given environment (``modify`` method).

Example
=======
In this example assume that we are in production environment. Administrator needs to enforce that all VM instances
will be deployed with secure key pair used for production environment.

Prior creating rules your OpenStack installation has to be configured as described in :ref:`policyenf_setup`.

Example rules
-------------

#. Create ``predeploy_modify`` rule

    Policy validation engine checks rule ``predeploy_modify`` and rules referenced inside this rule are evaluated by congress engine.

    .. code-block:: console

        predeploy_modify(eid, obj_id, action) :-
           murano:objects(obj_id, pid, type),
           murano:objects(eid, tid, "io.murano.Environment"),
           murano:connected(eid, pid),
           murano:properties(obj_id, "keyname", kn),
           concat("set-property: {object_id: ", obj_id, first_part),
           concat(first_part, ", prop_name: keyname, value: production-key}", action)
    ..

    Use this command to create the rule:

    .. code-block:: console

      congress policy rule create murano_system 'predeploy_modify(eid, obj_id, action):-murano:objects(obj_id, pid, type), murano_env_of_object(obj_id, eid), murano:properties(obj_id, "keyname", kn), concat("set-property: {object_id: ", obj_id, first_part), concat(first_part, ", prop_name: keyname, value: production-key}", action)'
    ..

    Key pair ``production-key`` must exists or change it to any existing key pair.

#. Deploy environment and check modification

    Deploy any environment and check that instances within the environment were deployed with the key pair specified above.
