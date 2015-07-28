.. _installation:

.. toctree::
   :maxdepth: 2

============
Installation
============

Network configuration
~~~~~~~~~~~~~~~~~~~~~

Policy configuration
~~~~~~~~~~~~~~~~~~~~

Like each service in OpenStack, murano has its own role-based access policies
that determine who and how can access objects. These policies are defined
in the service's :file:`policy.json` file.

On each API call corresponding policy check is performed.
:file:`policy.json` file can be changed whiteout interrupting the API service.

For detailed information on :file:`policy.json` syntax, please refer to the
`OpenStack official documentation <http://docs.openstack.org/kilo/config-reference/content/policy-json-file.html>`_

With this file you can set who may upload packages and perform other operations.

The :file:`policy.json` example is:

.. code-block:: javascript

    {
       // Rule declaration
       "context_is_admin": "role:admin",
       "admin_api": "is_admin:True",
       "default": "",

       // Package operations
       "get_package": "rule:default",
       "upload_package": "rule:default",
       "modify_package": "rule:default",
       "publicize_package": "rule:admin_api",
       "manage_public_package": "rule:default",
       "delete_package": "rule:default",
       "download_package": "rule:default",

       // Category operations
       "get_category": "rule:default",
       "delete_category": "rule:admin_api",
       "add_category": "rule:admin_api",

       // Deployment read operations
       "list_deployments": "rule:default",
       "statuses_deployments": "rule:default",

       // Environment operations
       "list_environments": "rule:default",
       "list_environments_all_tenants": "rule:admin_api",
       "show_environment": "rule:default",
       "update_environment": "rule:default",
       "create_environment": "rule:default",
       "delete_environment": "rule:default",

       // Environment template operations
       "list_env_templates": "rule:default",
       "create_env_template": "rule:default",
       "show_env_template": "rule:default",
       "update_env_template": "rule:default",
       "delete_env_template": "rule:default",

       // Control on executing actions on deployment environments
       "execute_action": "rule:default"
    }

So, changing ``"upload_package": "rule:default"`` to ``"rule:admin_api"``
will forbid regular users to upload packages.

Uploading package wizard in murano dashboard consists of several steps.
Upload package API call requested from the first form and modify from
the second one. It provides modifying package parameters on time of
uploading. So, please modify both configuration together. Otherwise it
will not be possible to browse package details on the second step
of the wizard.
