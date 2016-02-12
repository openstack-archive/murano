.. _policyenf_setup:

Setting up policy enforcement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you use the policy enforcement feature, configure Murano and Congress
properly.

.. note::

   This article does not cover Murano and Congress configuration options
   useful for Murano application deployment, for example, DNS setup,
   floating IPs, and so on.

**To enable policy enforcement, complete the following tasks:**

#. In Murano:

   * Enable the ``enable_model_policy_enforcer`` option
     in the ``murano.conf`` file:

    .. code-block:: ini

        [engine]
        # Enable model policy enforcer using Congress (boolean value)
        enable_model_policy_enforcer = true

    * Restart murano-engine.

#. Verify that Congress is installed and available in your OpenStack
   environment. See the details in the `Congress official documentation
   <http://congress.readthedocs.org/en/latest/>`_.

#. `Install the congress command-line client
   <http://docs.openstack.org/user-guide/common/cli_install_openstack_command_line_clients.html>`_
   as any other OpenStack command-line client.

#. For Congress, configure the following policies that policy enforcement uses
   during the evaluation:

   * ``murano`` policy

      It is created by the Congress` murano datasource driver, which is a part
      of Congress. Configure it for the OpenStack project (tenant) where you plan to
      deploy your Murano application. Datasource driver retrieves deployed
      Murano environments and populates Congress' murano policy tables.
      See :ref:`policyenf_dev` for details.

      Remove the existing ``murano`` policy and create a new ``murano`` policy
      configured for the ``demo`` project, by running:

      .. code-block:: console

         # remove default murano datasource configuration, because it is using 'admin' project. We need 'demo' project to be used.
         openstack congress datasource delete murano
         openstack congress datasource create murano murano --config username="$OS_USERNAME" --config tenant_name="demo"  --config password="$OS_PASSWORD" --config auth_url="$OS_AUTH_URL"

   * ``murano_system`` policy

      It holds the user-defined rules for policy enforcement. Typically,
      the rules use tables from other policies, for example, murano, nova,
      keystone, and others. Policy enforcement expects the ``predeploy_errors``
      table here that is available on the ``predeploy_errors`` rules creation.

      Create the ``murano_system`` rule, by running:

      .. code-block:: console

         # create murano_system policy
         openstack congress policy create murano_system

         # resolves objects within environment
         openstack congress policy rule create murano_system 'murano_env_of_object(oid,eid):-murano:connected(eid,oid), murano:objects(eid,tid,"io.murano.Environment")'

   * ``murano_action`` policy with internal management rules.

     These rules are used internally in the policy enforcement request
     and stored in a dedicated ``murano_action`` policy that is
     created here. They are important in case an environment is redeployed.

     .. code-block:: console

        # create murano_action policy
        openstack congress policy create murano_action --kind action

        # register action deleteEnv
        openstack congress policy rule create murano_action 'action("deleteEnv")'

        # states
        openstack congress policy rule create murano_action 'murano:states-(eid, st) :- deleteEnv(eid), murano:states( eid, st)'

        # parent_types
        openstack congress policy rule create murano_action 'murano:parent_types-(tid, type) :- deleteEnv(eid), murano:connected(eid, tid),murano:parent_types(tid,type)'
        openstack congress policy rule create murano_action 'murano:parent_types-(eid, type) :- deleteEnv(eid), murano:parent_types(eid,type)'

        # properties
        openstack congress policy rule create murano_action 'murano:properties-(oid, pn, pv) :- deleteEnv(eid), murano:connected(eid, oid), murano:properties(oid, pn, pv)'
        openstack congress policy rule create murano_action 'murano:properties-(eid, pn, pv) :- deleteEnv(eid), murano:properties(eid, pn, pv)'

        # objects
        openstack congress policy rule create murano_action 'murano:objects-(oid, pid, ot) :- deleteEnv(eid), murano:connected(eid, oid), murano:objects(oid, pid, ot)'
        openstack congress policy rule create murano_action 'murano:objects-(eid, tnid, ot) :- deleteEnv(eid), murano:objects(eid, tnid, ot)'

        # relationships
        openstack congress policy rule create murano_action 'murano:relationships-(sid, tid, rt) :- deleteEnv(eid), murano:connected(eid, sid), murano:relationships( sid, tid, rt)'
        openstack congress policy rule create murano_action 'murano:relationships-(eid, tid, rt) :- deleteEnv(eid), murano:relationships(eid, tid, rt)'

        # connected
        openstack congress policy rule create murano_action 'murano:connected-(tid, tid2) :- deleteEnv(eid), murano:connected(eid, tid), murano:connected(tid,tid2)'
        openstack congress policy rule create murano_action 'murano:connected-(eid, tid) :- deleteEnv(eid), murano:connected(eid,tid)'

