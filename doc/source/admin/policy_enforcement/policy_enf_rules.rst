.. _policy_enf_rules:

Creating policy enforcement rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This article illustrates how you can create policy enforcement rules.
For testing purposes, create rules that prohibit the creation
of instances with the flavor with over 2048 MB of RAM following
the procedure below.

**Procedure:**

#. Verify that you have configured your OpenStack environment as described
   in :ref:`policyenf_setup`.

#. To create the ``predeploy_errors`` rule, run:

   .. code-block:: console

      congress policy rule create murano_system "predeploy_errors(eid, obj_id, msg) :- murano:objects(obj_id, pid, type), murano:objects(eid, tid, \"io.murano.Environment\"), murano:connected(eid, pid), murano:properties(obj_id, \"flavor\", flavor_name), flavor_ram(flavor_name, ram), gt(ram, 2048), murano:properties(obj_id, \"name\", obj_name), concat(obj_name, \": instance flavor has RAM size over 2048MB\", msg)"

   The command above contains the following information:

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

   Policy validation engine checks the ``predeploy_errors`` rule, and rules
   referenced within this rule are evaluated by the Congress engine.

   In this example, we create the rule that references the ``flavor_ram``
   rule we create afterwards. It disables flavors with RAM more than
   2048 MB and constructs the message returned to the user
   in the ``msg`` variable.

   In this example we use data from policy **murano** which is represented by
   ``murano:properties``. There are stored rows with decomposition of model
   representing murano application. We also use built-in functions of Congress:

   * ``gt`` stands for 'greater-than'
   * ``concat`` joins two strings into one variable

#. To create the ``flavor_ram`` rule, run:

   .. code-block:: console

      congress policy rule create murano_system "flavor_ram(flavor_name, ram) :- nova:flavors(id, flavor_name, cpus, ram)"

   This rule resolves parameters of flavor by flavor name and returns
   the ``ram`` parameter. It uses the ``flavors`` rule from ``nova`` policy.
   Data in this policy is filled by the ``nova`` datasource driver.

#. Check the rule usage.

   #. Create an environment with a simple application:

      - Select an application from the murano applications.
      - Create a ``m1.medium`` instance, which uses 4096 MB RAM.

      .. image:: ../figures/new-inst.png
         :alt: Create new instance
         :width: 100 %

   #. Deploy the environment.

Deployment fails as the rule is violated: environment is in the ``Deploy
FAILURE`` status. Check the deployment logs for details:

.. image:: ../figures/deploy-log.png
   :alt: Deployment log
   :width: 100 %


.. seealso::

   * :ref:`base_mod_rules`
