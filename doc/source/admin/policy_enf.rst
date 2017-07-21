.. _policy_enf:

=================================
Policy enforcement using Congress
=================================

Policies are defined and evaluated in the Congress_ project.
The policy language for Congress is Datalog. The congress policy consists
of the Datalog rules and facts.

Examples of policies are as follows:

* Minimum 2 GB of RAM for all VM instances.
* A certified version for all Apache server instances.
* Data placement policy: all database instances must be deployed at a given
  geographic location enforcing some law restriction on data placement.

These policies are evaluated over data in the form of tables (Congress data
structures). A deployed Murano environment must be decomposed to the Congress
data structures. The decomposed environment is sent to Congress for simulation.
Congress simulates whether the resulting state violates any defined
policy: deployment is aborted in case of policy violation.

Murano uses two predefined policies in Congress:

* ``murano_system`` contains rules and facts of policies defined by the cloud
  administrator.
* ``murano`` contains only facts/records reflecting the resulting state after
  the deployment of an environment.

Records in the ``murano`` policy are queried by rules from
the ``murano_system`` policy. The Congress simulation does not create any
records in the ``murano`` policy, and only provides the feedback on whether
the resulting state violates the policy or not.

As a part of the policy guided fulfillment, you need to enforce policies
on a murano environment deployment. If the policy enforcement fails,
the deployment fails as well.

.. _Congress: https://wiki.openstack.org/wiki/Congress

This section contains the following subsections:

.. toctree::
   :maxdepth: 2

   policy_enforcement/policy_enf_setup
   policy_enforcement/policy_enf_rules
   policy_enforcement/policy_enf_dev
   policy_enforcement/policy_enf_modify

