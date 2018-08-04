.. _admin-troubleshooting:

===============
Troubleshooting
===============

Log location
~~~~~~~~~~~~

By default, logs are sent to stdout. Consider how to set up the log files.

Murano API + Engine
-------------------

To define a file where to store logs, use the ``log_file`` option in the
:file:`murano.conf` file. You can provide an absolute or a relative path.

To enable a detailed log file configuration, set up :file:`logging.conf`.
The example is provided in :file:`etc/murano` directory. The log configuration
file location is set with the ``log_config_append`` option in the murano
configuration file.

Murano applications
-------------------

Murano applications have a separate logging handler and a separate file where
all logs from application definitions should be provided. Open the
:file:`logging.conf` file and check the ``args: ('applications.log',)``
option in the ``handler_applications`` section.

Verify that ``log_config_append`` is not empty and set to the
:file:`logging.conf` location.

Issues during configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If any issues occur, first of all verify the following:

* All murano components have consistent versions: murano-dashboard and
  murano-engine should use the same or compatible python-muranoclient version.
  Dependent component versions can be found in :file:`requirements.txt` file.

* The database is synced with code by running:

  .. code-block:: console

     murano-db-manage --config-file murano.conf upgrade

**Failed to execute `murano-db-manage`**

* Make sure the ``--config-file`` option is provided.
* Check `connection` parameter in the provided configuration file. It should
  be a `connection string <http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html>`_.

* Check that MySQL or PostgreSQL (depending of what you provided in the
  connection string) Python modules are installed on the system.

**Applications panel is not seen in horizon**

* Make sure that the following files are copied to the
  ``openstack_dashboard/local/enabled`` directory, and _50_murano.py is copied
  to ``openstack_dashboard/local/local_settings.d`` directory.

  * _50_dashboard_catalog.py
  * _51_muranodashboard.py
  * _60_panel_group_browse.py
  * _63_panel_murano_catalog.py
  * _70_panel_group_manage.py
  * _71_panel_murano_packages.py
  * _72_panel_murano_images.py
  * _73_panel_murano_categories.py
  * _80_panel_group_applications.py
  * _81_panel_applications_environments.py

* Check that murano data is not inserted twice in the settings file and as a
  plugin.

**Applications panel can be browsed, but 'Unable to communicate to murano-api server.' appears**

If you have murano registered in keystone, verify the endpoint URL is valid
and service has *application-catalog* name. If you do not want to register the
murano service in keystone, just add ``MURANO_API_URL`` option to the horizon
local setting.

Issues during deployment
~~~~~~~~~~~~~~~~~~~~~~~~

Besides identifying errors from log files, there is another and more flexible
way to browse deployment errors -- directly from UI. When the *Deploy Failed*
status appears, navigate to :menuselection:`Environment Components` and click
the :guilabel:`Latest Deployment Log` tab. You can see steps of the deployment
and the one that failed would have red color.

**while scanning a simple key in "<string>", line 32, column 3: ...**

There is an error in the YAML file format. Before uploading a package,
validate your file in an online YAML validator like
`YAMLint <http://www.yamllint.com/>`_.
Later `validation tool <https://blueprints.launchpad.net/murano/+spec/murano-package-verification-tool>`_
to check package closely while uploading will be added.

**NoPackageForClassFound: Package for class io.murano.Environment is not found**

Verify that murano core package is uploaded. If not, the content of the
``meta/io.murano`` folder should be zipped and uploaded to Murano.

**[keystoneclient.exceptions.AuthorizationFailure]:**
**Authorization failed: You are not authorized to perform the requested action. (HTTP 403)**

The token expires during the deployment. Usually the default standard token
lifetime is one hour. The error occurs frequently as, in most cases, a
deployment takes longer than that or does not start right after a token is
generated.

Workarounds:

* Use trusts. Only possible in the v3 version. Read more in the
  `official documentation <https://wiki.openstack.org/wiki/Keystone/Trusts>`_
  or `here <https://docs.openstack.org/heat/latest/admin/auth-model.html>`_.
  Do not forget to check the corresponding heat and murano settings. Trusts
  are enabled by default in murano and heat since Kilo release.

  In murano, the corresponding configuration option is located in the
  ``engine`` section:

  .. code-block:: ini

     [engine]

     ...

     # Create resources using trust token rather than user's token (boolean
     # value)
     use_trusts = true

  If your Keystone runs v2 version, see the solutions below.

* Make logout/login to compose a new token and start the deployment again.
  Would not help for long deployment or if the token lifetime is too small.

* Increase the token lifetime in the keystone configuration file.

**The murano-agent did not respond within 3600 seconds**

* Check transport access to the virtual machine: verify that the router has a
  gateway.
* Check the RabbitMQ settings: verify that the agent has valid RabbitMQ
  parameters.
  Go to the spawned virtual machine and open :file:`*/etc/murano/agent.conf`
  on the Linux-based machine or :file:`C:\\Murano\\Agent\\agent.conf` on the
  Windows-based machine. Additionally, you can examine agent logs that by
  default are located at :file:`/var/log/murano-agent.log` The first part of
  the log file contains reconnection attempts to the RabbitMQ since the valid
  RabbitMQ address and queue have not been obtained yet.
* Verify that the ``driver`` option in ``[oslo_messaging_notifications]`` group
  is set to ``messagingv2``.

**murano.engine.system.agent.AgentException**

The agent started the execution plan but something went wrong. Examine agent
logs (see the previous paragraph for the logs placement information). Also,
try to manually execute the application scripts.

**[exceptions.EnvironmentError]: Unexpected stack state NOT_FOUND or UPDATE_FAILED**

An issue with heat stack creation, examine the heat log file. Try to manually
spawn the instance. If the reason of the stack creation fail is ``no valid
host was found``, there might be not enough resources or something is wrong
with the nova-scheduler.

**Router could not be created, no external network found**

Find the ``external_network`` parameter in the ``networking`` section of the
murano configuration file and verify that the specified external network does
exist through Web UI or by executing the
:command:`openstack network list --external` command.

**Deployment log in the UI contains incomplete reports**

Sometimes logs contain only two messages after the application deployment.
There are no messages provided in applications themselves:

.. code-block:: console

  2015-09-21 11:14:58 — Action deploy is scheduled
  2015-09-21 11:16:43 — Deployment finished successfully

To fix the issue, set the ``driver`` option in the :file:`murano.config` file
to ``messagingv2``.
