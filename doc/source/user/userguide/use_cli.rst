.. _use-cli:

=========
Using CLI
=========

This section provides murano end users with information on how they can use
the Application Catalog through the command-line interface (CLI).

Using python-muranoclient, the CLI client for murano, you can easily manage
your environments, packages, categories, and deploy environments.

.. toctree::
   :maxdepth: 1

   install_client

Manage environments
~~~~~~~~~~~~~~~~~~~

An environment is a set of logically connected applications that are grouped
together for an easy management. By default, each environment has a single
network for all its applications, and the deployment of the environment is
defined in a single heat stack. Applications in different environments are
always independent from one another.

An environment is a single unit of deployment. This means that you deploy not
an application but an environment that contains one or multiple applications.

Using CLI, you can easily perform such actions with an environment as
creating, renaming, editing, viewing, and others.

Create an environment
---------------------

To create an environment, use the following command specifying the
environment name:

.. code-block:: console

   $ murano environment-create <NAME>

Rename an environment
---------------------

To rename an environment, use the following command specifying the old name of
the environment or its ID and the new name:

.. code-block:: console

   $ murano environment-rename <OLD_NAME_OR_ID> <NEW_NAME>

Delete an environment
---------------------

To delete an environment, use the following command specifying the
environment name or ID:

.. code-block:: console

   $ murano environment-delete <NAME_OR_ID>

List deployments for an environment
-----------------------------------

To get a list of deployments for a particular environment, use the following
command specifying the environment name or ID:

.. code-block:: console

   $ murano deployment-list <NAME_OR_ID>

List the environments
---------------------

To get a list of all existing environments, run:

.. code-block:: console

   $ murano environment-list

Show environment object model
-----------------------------

To get a complete object model of the environment, run:

.. code-block:: console

   $ murano environment-model-show <ID>

To get some part of the environment model, run:

.. code-block:: console

   $ murano environment-model-show <ID> --path <PATH>

For example:

   $ murano environment-model-show 534bcf2f2fc244f2b94ad55ff0f24a42 --path /defaultNetworks/environment

To get a draft of an object model of environment in pending state, also
specify id of the session:

.. code-block:: console

   $ murano environment-model-show <ID> --path <PATH> --session-id <SESSION_ID>

Edit environment object model
-----------------------------

To edit an object model of the environment, run:

.. code-block:: console

   $ murano environment-model-edit <ID> <FILE> --session-id <SESSION_ID>

<FILE> is the path to the file with the JSON-patch to modify the object model.

JSON-patch is a valid JSON that contains a list of changes to be applied to
the current object. Each change contains a dictionary with three keys: ``op``,
``path`` and ``value``. ``op`` (operation) can be one of the three values:
`add`, `replace` or remove`.

Allowed operations for paths:

* "" (model root): no operations
* "defaultNetworks": "replace"
* "defaultNetworks/environment": "replace"
* "defaultNetworks/environment/?/id": no operations
* "defaultNetworks/flat": "replace"
* "name": "replace"
* "region": "replace"
* "?/type": "replace"
* "?/id": no operations

For other paths any operation (add, replace or remove) is allowed.

Example of JSON-patch:

.. code-block:: javascript

   [{
     "op": "replace",
     "path": "/defaultNetworks/flat",
     "value": true
   }]

The patch above changes the value of the ``flat`` property of the
environment's ``defaultNetworks`` property to `true`.

Manage packages
~~~~~~~~~~~~~~~

This section describes how to manage packages using the command line
interface. You can easily:

* :ref:`import a package <cli_import>` or :ref:`bundles of packages <cli_bundles>`
* :ref:`list the existing packages <cli_list>`
* :ref:`display details for a package <cli_display>`
* :ref:`download a package <cli_download>`
* :ref:`delete a package <cli_delete>`
* :ref:`create a package <cli_create>`

.. _cli_import:

Import a package
----------------

With the :command:`package-import` command you can import packages
into murano in several different ways:

* :ref:`from a local .zip file <cli_zip>`
* :ref:`from murano app repository <cli_repo>`
* :ref:`from an http URL <cli_url>`

.. _cli_zip:

**From a local .zip file**

To import a package from a local .zip file, run:

.. code-block:: console

  $ murano package-import /path/to/PACKAGE.zip

where ``PACKAGE`` is the name of the package stored on your
computer.

For example:

.. code-block:: console

  $ murano package-import /home/downloads/mysql.zip
  Importing package com.example.databases.MySql
  +---------------------------------+------+----------------------------+--------------+---------+
  | ID                              | Name | FQN                        | Author       |Is Public|
  +---------------------------------+------+----------------------------+--------------+---------+
  | 83e4038885c248e3a758f8217ff8241f| MySQL| com.example.databases.MySql| Mirantis, Inc|         |
  +---------------------------------+------+----------------------------+--------------+---------+

To make the package available for users from other projects (tenants), use the
``--is-public`` parameter. For example:

.. code-block:: console

   $ murano package-import --is-public mysql.zip

.. note::

   The :command:`package-import` command supports multiple positional
   arguments. This means that you can import several packages at once.

.. _cli_repo:

**From murano app repository**

.. |link_location| raw:: html

   <a href="http://apps.openstack.org/#tab=murano-apps" target="_blank">murano applications repository</a>

To import a package from murano applications repository, specify
the URL of the repository with ``--murano-repo-url`` and a fully
qualified package name. For package names, go to |link_location|,
and click on the desired package to see its full name.

.. note::

   You can also specify the URL of the repository with the
   corresponding MURANO_REPO_URL environment variable.


The following example shows how to import the MySQL package from the
murano applications repository:

.. code-block:: console

   $ murano --murano-repo-url=http://storage.apps.openstack.org \
   package-import com.example.databases.MySql

This command supports an optional ``--package-version`` parameter that instructs
murano client to download a specified package version.

The :command:`package-import` command inspects package requirements
specified in the package's manifest under the *Require* section, and
attempts to import them from murano repository. The :command:`package-import`
command also inspects any image prerequisites mentioned in the
:file:`images.lst` file in the package. If there are any image
requirements, client would inspect images already present in the image
database. Unless image with the specific name is present, client would
attempt to download it.

.. TODO: Add a ref link to step-by-step (on specifying images and requirements
   for packages).


If any of the packages being installed is already registered in murano,
the client asks you what to do with it. You can specify the default action
with ``--exists-action``, passing ``s`` - for skip, ``u`` - for update, and
``a`` - for abort.

.. _cli_url:

**From an URL**

To import an application package from an URL, use the following command:

.. code-block:: console

  $ murano package-import http://example.com/path/to/PACKAGE.zip

The example below shows how to import a MySQL package from the
murano applications repository using the package URL:

.. code-block:: console

  $ murano package-import http://storage.apps.openstack.org/apps/com.example.databases.MySql.zip
  Inspecting required images
  Importing package com.example.databases.MySql
  +----------------------------------+-------+----------------------------+--------------+--------+----------+------------+
  | ID                               | Name  | FQN                        | Author       | Active | Is Public| Type       |
  +----------------------------------+-------+----------------------------+--------------+--------+----------+------------+
  | 1aa62196595f411399e4e48cc2f6a512 | MySQL | com.example.databases.MySql| Mirantis, Inc| True   |          | Application|
  +----------------------------------+-------+----------------------------+--------------+--------+----------+------------+

.. _cli_bundles:

Import bundles of packages
--------------------------

With the :command:`bundle-import` command you can install packages in
several different ways:

* :ref:`from a local bundle <cli_local_bundle>`
* :ref:`from an URL <cli_bundle_url>`
* :ref:`from murano app repository <cli_bundle_repo>`

When importing bundles, you can set their publicity with ``--is-public``.

.. _cli_local_bundle:

**From a local bundle**

To import a bundle from the a local file system, use the following
command:

.. code-block:: console

  $ murano bundle-import /path/to/bundle/BUNDLE_NAME

This command imports all the requirements of packages and
images.

When importing a bundle from a file system, the murano client
searches for packages in a directory relative to the bundle location
before attempting to download a package from repository. This facilitates
cases with no Internet access.

The following example shows the import of a monitoring bundle:

.. code-block:: console

 $ murano bundle-import /home/downloads/monitoring.bundle
 Inspecting required images
 Importing package com.example.ZabbixServer
 Importing package com.example.ZabbixAgent
 +----------------------------------+---------------+--------------------------+---------------+--------+----------+------------+
 | ID                               | Name          | FQN                      | Author        | Active | Is Public| Type       |
 +----------------------------------+---------------+--------------------------+---------------+--------+----------+------------+
 | fb0b35359e384fe18158ff3ed8f969b5 | Zabbix Agent  | com.example.ZabbixAgent  | Mirantis, Inc | True   |          | Application|
 | 00a77e302a65420c8080dc97cc0f2723 | Zabbix Server | com.example.ZabbixServer | Mirantis, Inc | True   |          | Application|
 +----------------------------------+---------------+--------------------------+---------------+--------+----------+------------+

.. note::

   The :command:`bundle-import` command supports multiple positional
   arguments. This means that you can import several bundles at once.

.. _cli_bundle_url:

**From an URL**

To import a bundle from an URL, use the following command:

.. code-block:: console

  $ murano bundle-import http://example.com/path/to/bundle/BUNDLE_NAME

Where ``http://example.com/path/to/bundle/BUNDLE_NAME`` is any external http/https
URL to load the bundle from.

For example:

.. code-block:: console

  $ murano bundle-import http://storage.apps.openstack.org/bundles/monitoring.bundle

.. _cli_bundle_repo:

**From murano applications repository**

To import a bundle from murano applications repository, use the
following command, where ``bundle_name`` stands for the bundle name:

.. code-block:: console

  $ murano bundle-import BUNDLE_NAME

For example:

.. code-block:: console

  $ murano bundle-import monitoring

.. |location| raw:: html

   <a href="http://apps.openstack.org/#tab=murano-apps" target="_blank">murano applications repository</a>

.. note::

   For bundle names, go to |location|, click the
   **Format** tab to show bundles first, and then click on
   the desired bundle to see its name.

.. _cli_list:

List packages
-------------

To list all the existing packages you have, use the
:command:`package-list` command. The result will show you the package
ID, name, author and if it is public or not. For example:

.. code-block:: console

 $ murano package-list
 +----------------------------------+--------------------+-------------------------------------+---------------+--------+----------+------------+
 | ID                               | Name               | FQN                                 | Author        | Active | Is Public| Type       |
 +----------------------------------+--------------------+-------------------------------------+---------------+--------+----------+------------+
 | daa46cfd78c74c11bcbe66d3239e546e | Apache HTTP Server | com.example.apache.ApacheHttpServer | Mirantis, Inc | True   |          | Application|
 | 5252c9897e864c9f940e08500056f155 | Cloud Foundry      | com.example.paas.CloudFoundry       | Mirantis, Inc | True   |          | Application|
 | 1aa62196595f411399e4e48cc2f6a512 | MySQL              | com.example.databases.MySql         | Mirantis, Inc | True   |          | Application|
 | 11d73cfdc6d7447a910984d95090463b | SQL Library        | com.example.databases               | Mirantis, Inc | True   |          | Application|
 | fb0b35359e384fe18158ff3ed8f969b5 | Zabbix Agent       | com.example.ZabbixAgent             | Mirantis, Inc | True   |          | Application|
 | 00a77e302a65420c8080dc97cc0f2723 | Zabbix Server      | com.example.ZabbixServer            | Mirantis, Inc | True   |          | Application|
 +----------------------------------+--------------------+-------------------------------------+---------------+--------+----------+------------+

.. _cli_display:

Show packages
-------------

To get full information about a package, use the :command:`package-show`
command. For example:

.. code-block:: console

 $ murano package-show 1aa62196595f411399e4e48cc2f6a512
 +----------------------+-----------------------------------------------------+
 | Property             | Value                                               |
 +----------------------+-----------------------------------------------------+
 | categories           |                                                     |
 | class_definitions    | com.example.databases.MySql                         |
 | description          | MySql is a relational database management system    |
 |                      | (RDBMS), and ships with no GUI tools to administer  |
 |                      | MySQL databases or manage data contained within the |
 |                      | databases.                                          |
 | enabled              | True                                                |
 | fully_qualified_name | com.example.databases.MySql                         |
 | id                   | 1aa62196595f411399e4e48cc2f6a512                    |
 | is_public            | False                                               |
 | name                 | MySQL                                               |
 | owner_id             | 1ddb2c610d4e4c5dab5185e32554560a                    |
 | tags                 | Database, MySql, SQL, RDBMS                         |
 | type                 | Application                                         |
 +----------------------+-----------------------------------------------------+

.. _cli_delete:

Delete a package
----------------

To delete a package, use the following command:

.. code-block:: console

  $ murano package-delete PACKAGE_ID

.. _cli_download:

Download a package
------------------

With the following command you can download a .zip archive
with a specified package:

.. code-block:: console

  $ murano package-download PACKAGE_ID > FILE.zip

You need to specify the package ID and enter the .zip file name
under which to save the package.

For example:

.. code-block:: console

  $ murano package-download e44a3f526dfb4e08b3c1018c9968d911 > Wordpress.zip

.. _cli_create:

Create a package
----------------

With the murano client you can create application packages from package
source files or directories. The :command:`package-create` command is
useful when application package files are spread across several directories.
This command has the following required parameters::

 -r RESOURCES_DIRECTORY
 -c CLASSES_DIRECTORY
 --type TYPE
 -o PACKAGE_NAME.zip
 -f FULL_NAME
 -n DISPLAY_NAME

Example:

.. code-block:: console

  $ murano package-create -c Downloads/Folder1/Classes -r Downloads/Folder2/Resources \
  -n mysql -f com.example.MySQL -d Package -o MySQL.zip --type Library
  Application package is available at /home/Downloads/MySQL.zip

After this, the package is ready to be imported to the application
catalog.

The :command:`package-create` command is also useful for autogenerating
packages from heat templates. In this case you do not need to manually
specify so many parameters. For more information on automatic package
composition, please see :ref:`Automatic package composing <compose_package>`.

Manage categories
~~~~~~~~~~~~~~~~~

In murano, applications can belong to a category or multiple categories.
Administrative users can create and delete a category as well as list
available categories and view details for a particular category.

Create a category
-----------------

To create a category, use the following command specifying the category name:

.. code-block:: console

   $ murano category-create <NAME>

List available categories
-------------------------

To get a list of all existing categories, run:

.. code-block:: console

   $ murano category-list

Show category details
---------------------

To see packages that belong to a particular category, use the following
command specifying the category ID:

.. code-block:: console

   $ murano category-show <ID>

Delete a category
-----------------

To delete a category, use the following command specifying the ID of a
category or multiple categories to delete:

.. code-block:: console

   $ murano category-delete <ID> [<ID> ...]

.. note::

   Verify that no packages belong to the category to be deleted, otherwise an
   error appears. For this, use the :command:`murano category-show <ID>`
   command.

Manage environment templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To manage environment templates, use the following commands specifying
appropriate values:

:command:`murano env-template-create <ENV_TEMPLATE_NAME>`
 Creates an environment template.

:command:`murano env-template-clone <ID> <NEW_ENV_TEMPLATE_NAME>`
 Creates a new template, cloned from an existing template.

:command:`murano env-template-create-env <ID> <ENV_TEMPLATE_NAME>`
 Creates a new environment from template.

:command:`murano env-template-add-app <ENV_TEMPLATE_ID> <FILE>`
 Adds an application or multiple applications to the environment template.

:command:`murano env-template-del-app <ENV_TEMPLATE_ID> <ENV_TEMPLATE_APP_ID>`
 Deletes an application from the environment template.

:command:`murano env-template-list`
 Lists the environments templates.

:command:`murano env-template-show <ID>`
 Displays environment template details.

:command:`murano env-template-update <ID> <ENV_TEMPLATE_NAME>`
 Updates an environment template.

:command:`murano env-template-delete <ID>`
 Deletes an environment template.

.. seealso::
   `Application Catalog service command-line client <http://docs.openstack.org/cli-reference/murano.html>`_.
