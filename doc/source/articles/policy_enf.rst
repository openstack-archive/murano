=================================
Murano Policy Enforcement Example
=================================

Introduction
============
As a part of the policy guided fulfillment, we need to enforce policies on the Murano environment deployment.
If the policy enforcement failed, deployment fails. Policies are defined and evaluated in the Congress_ project.
The policy language for Congress is Datalog. The congress policy consists of Datalog rules and facts.
The cloud administrator defines policies in Congress. Examples of such policies:

* all VM instances must have at least 2GB of RAM
* all Apache server instances must have given certified version
* data placement policy: all DB instances must be deployed at given geo location (enforcing some law restriction on data placement)

These policies are evaluated over data in the form of tables (Congress data structures). A deployed Murano environment must be
decomposed to Congress data structures. The decomposed environment is sent to congress for simulation. Congress simulates
whether the resulting state does not violate any defined policy. Deployment is aborted in case of policy violation.
Murano uses two predefined policies in Congress:

* *murano_system* contains rules and facts of policies defined by cloud admin.
* *murano* contains only facts/records reflecting resulting state after deployment of an environment.

Records in the *murano* policy are queried by rules from the *murano_system* policy. The congress simulation does not create any
records in the *murano* policy. Congress will only give feedback on whether the resulting state violates the policy or not.

.. _Congress: https://wiki.openstack.org/wiki/Congress

Example
=======
In this example we will create rules that prohibit creating VM instances with flavor with more than 2048 MB ram.

Prior creating rules your OpenStack installation has to be configured as described in :ref:`policyenf_setup`.

Example rules
-------------

#. Create ``predeploy_errors`` rule

    Policy validation engine checks rule ``predeploy_errors`` and rules referenced inside this rule are evaluated by congress engine.

    We create example rule which references ``flavor_ram`` rule we create afterwards. It disables flavors with ram higher than 2048 MB and constructs message returned to the user in *msg* variable.

    .. code-block:: console

        predeploy_errors(eid, obj_id, msg) :-
           murano:objects(obj_id, pid, type),
           murano:objects(eid, tid, "io.murano.Environment"),
           murano:connected(eid, pid),
           murano:properties(obj_id, "flavor", flavor_name),
           flavor_ram(flavor_name, ram),
           gt(ram, 2048),
           murano:properties(obj_id, "name", obj_name),
           concat(obj_name, ": instance flavor has RAM size over 2048MB", msg)
    ..

    Use this command to create the rule:

    .. code-block:: console

      congress policy rule create murano_system "predeploy_errors(eid, obj_id, msg) :- murano:objects(obj_id, pid, type), murano:objects(eid, tid, \"io.murano.Environment\"), murano:connected(eid, pid), murano:properties(obj_id, \"flavor\", flavor_name), flavor_ram(flavor_name, ram), gt(ram, 2048), murano:properties(obj_id, \"name\", obj_name), concat(obj_name, \": instance flavor has RAM size over 2048MB\", msg)"
    ..

    In this example we used data from policy **murano** which is represented by ``murano:properties``. There are stored rows with decomposition of model representing murano application. We also used built-in functions of congress - ``gt`` - greater-than, and ``concat`` which joins two strings into variable.

#. Create ``flavor_ram`` rule

    We create the rule that resolves parameters of flavor by flavor name and returns *ram* parameter. It uses rule *flavors* from *nova* policy. Data in this policy is filled by *nova* datasource driver.

    Use this command to create the rule:

    .. code-block:: console

        congress policy rule create murano_system "flavor_ram(flavor_name, ram) :- nova:flavors(id, flavor_name, cpus, ram)"
    ..

Example rules in murano app deployment
--------------------------------------

#. Create environment with simple application

    - Choose Git application from murano applications
    - Create with **"m1.medium"** instance flavor which uses 4096MB so validation will fail

    .. image:: new-instance.png


#. Deploy environment

    - Environment is in Status: **Deploy FAILURE**
    - Check deployment log:

    .. image:: deployment-log.png