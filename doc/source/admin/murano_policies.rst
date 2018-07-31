.. _murano_policies:

===============
Murano Policies
===============

Murano only uses 2 roles for policy enforcement. Murano allows access by
default and uses the admin role for any action that involves accessing
data across multiple projects in the cloud.

.. glossary::

    role:Member
        User is non-admin to all APIs.

    role:admin
        User is admin to all APIs.

Sample File Generation
----------------------

To generate a sample policy.yaml file from the Murano defaults, run the
oslo policy generation script::

    oslopolicy-sample-generator \
    --config-file etc/oslo-policy-generator/murano-policy-generator.conf \
    --output-file policy.yaml.sample

or using tox::

    tox -egenpolicy

.. note::

  In previous OpenStack releases the default policy format was JSON, but
  now the `recommended format <https://docs.openstack.org/ocata/config-reference/policy-yaml-file.html#older-json-format-policy>`_
  is YAML.
..

Merged File Generation
----------------------

This will output a policy file which includes all registered policy defaults
and all policies configured with a policy file. This file shows the effective
policy in use by the project::

    oslopolicy-sample-generator \
    --config-file etc/oslo-policy-generator/murano-policy-generator.conf

List Redundant Configurations
-----------------------------

This will output a list of matches for policy rules that are defined in a
configuration file where the rule does not differ from a registered default
rule. These are rules that can be removed from the policy file with no change
in effective policy::

    oslopolicy-list-redundant \
    --config-file etc/oslo-policy-generator/murano-policy-generator.conf

Policy configuration
--------------------

Like each service in OpenStack, Murano has its own role-based access policies
that determine who can access objects and under what circumstances. The default
implementation for these policies is defined in the service's source code --
under :file:`murano.common.policies`. The default policy definitions can be
overridden using the :file:`policy.yaml` file.

On each API call the corresponding policy check is performed.
:file:`policy.yaml` file can be changed without interrupting the API service.

For detailed information on :file:`policy.yaml` syntax, please refer to the
`OpenStack official documentation <https://docs.openstack.org/ocata/config-reference/policy-yaml-file.html>`_

With this file you can set who may upload packages and perform other operations.

So, changing ``"upload_package": "rule:default"`` to ``"rule:admin_api"``
will forbid regular users from uploading packages.

For reference:

- ``"get_package"`` is checked whenever a user accesses a package
  from the catalog. default: anyone
- ``"upload_package"`` is checked whenever a user uploads a package
  to the catalog.  default: anyone
- ``"modify_package"`` is checked whenever a user modifies a package
  in the catalog. default: anyone
- ``"publicize_package"`` is checked whenever a user is trying to
  make a murano package public (both when creating a new package or
  modifying an existing one). default: admin users
- ``"manage_public_package"`` is checked whenever a user attempts to
  modify parameters of a public package. default: admin users
- ``"delete_package"`` is checked whenever a user attempts to
  delete a package from the catalog. default: anyone
- ``"download_package"`` is checked whenever a user attempts to
  download a package from the catalog. default: anyone
- ``"list_environments_all_tenants"`` is checked whenever a request
  to list environments of all tenants is made. default: admin users
- ``"execute_action"`` is checked whenever a user attempts to execute
  an action on deployment environments. default: anyone

.. note::

  The package upload wizard in Murano dashboard consists of several steps:
  The "upload_package" policy is enforced during the first step while
  "modify_package" is enforced during the second step. Package parameters are
  modified during package upload. So, please modify both policy definitions
  together. Otherwise it will not be possible to browse package details on the
  second step of the wizard.

Default Murano Policies
-----------------------

.. literalinclude:: ../_static/murano.policy.yaml.sample
