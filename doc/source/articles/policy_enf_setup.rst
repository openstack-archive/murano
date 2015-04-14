=====================================
Murano Policy Enforcement Setup Guide
=====================================

.. _policyenf_setup:

Introduction
------------

Before policy enforcement feature will be used, it has to be configured. It has
to be enabled in Murano configuration, and Congress has to have created policy
and rules used during policy evaluation.

This document does not cover Murano and Congress configuration options useful
for Murano application deployment (e.g., DNS setup, floating IPs, ...).

Setup
-----

This setup uses *openstack* command. You can use copy-paste for commands.

If you are using DevStack installation, you can setup environment using
following command.

   .. code-block:: ini

      source devstack/openrc admin admin
   ..

#. **Murano**

   Enable policy enforcement in Murano:

    - edit */etc/murano/murano.conf* to enable **enable_model_policy_enforcer**
      option:

    .. code-block:: ini

        [engine]
        # Enable model policy enforcer using Congress (boolean value)
        enable_model_policy_enforcer = true
    ..

    - restart murano-engine

#. **Congress**

   Policy enforcement uses following policies:

   - **murano** policy

      Policy is created by Congress' Murano datasource driver, which is part of
      Congress. It has to be configured for the OpenStack tenant where Murano
      application will be deployed. Datasource driver retrieves deployed Murano
      environments and populates Congress' murano policy tables
      (:ref:`policyenf_dev`).

      Following commands removes existing **murano** policy, and creates new
      **murano** policy configured for tenant *demo*.

   .. code-block:: console

      . ~/devstack/openrc admin admin # if you are using devstack, otherwise you have to setup env manually

      # remove default murano datasource configuration, because it is using 'admin' tenant. We need 'demo' tenant to be used.
      openstack congress datasource delete murano
      openstack congress datasource create murano murano --config username="$OS_USERNAME" --config tenant_name="demo"  --config password="$OS_PASSWORD" --config auth_url="$OS_AUTH_URL"
   ..

   - **murano_system** policy
      Policy holds user defined rules for policy enforcement. Rules typically
      uses tables from other policies (e.g., murano, nova, keystone, ...).
      Policy enforcement expects *predeploy_errors* table here which is created
      by creating **predeploy_errors** rules.

      Following command creates **murano_system** rule

   .. code-block:: console

      openstack congress policy create murano_system
   ..

   - **murano_action** policy with internal management rules
      Following rules are used internally in policy enforcement request.
      These rules are stored in dedicated **murano_action** policy which is
      created here.
      They are important for case when an environment is deployed again.

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
   ..
