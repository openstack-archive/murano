..
      Copyright 2015 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http//www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _client:

=============
Murano client
=============

Module python-muranoclient comes with CLI *murano* utility, that interacts with
Murano application catalog

Installation
============

To install latest murano CLI client run the following command in your shell::

    pip install python-muranoclient

Alternatively you can checkout the latest version from
https://git.openstack.org/cgit/openstack/python-muranoclient


Using CLI client
================

In order to use the CLI, you must provide your OpenStack username, password,
tenant name or id, and auth endpoint. Use the corresponding arguments
(``--os-username``, ``--os-password``, ``--os-tenant-name`` or
``--os-tenant-id``, ``--os-auth-url`` and ``--murano-url``) or
set corresponding environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=password
    export OS_TENANT_NAME=tenant
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0
    export MURANO_URL=http://murano.example.com:8082/

Once you've configured your authentication parameters, you can run ``murano
help`` to see a complete listing of available commands and arguments and
``murano help <sub_command>`` to get help on specific subcommand.


Bash completion
===============

To get the latest bash completion script download `murano.bash_completion`_
from the source repository and add it to your completion scripts.


.. _murano.bash_completion: https://git.openstack.org/cgit/openstack/python-muranoclient/plain/tools/murano.bash_completion


Listing currently installed packages
====================================

To get list of currently installed packages run::

    murano package-list

To show details about specific package run::

    murano package-show <PKG_ID>

Importing packages in Murano
============================

``package-import`` subcommand can install packages in several different ways:
    * from a locall file
    * from a http url
    * from murano app repository

When creating a package you can specify it's categories with
``-c/--categories`` and set it's publicity with ``--public``

To import a local package run::

    murano package-import /path/to/package.zip

To import a package from http url run::

    murano package-import http://example.com/path/to/package.zip

And finally you can import a package from Murano repository. To do so you have
to specify base url for the repository with ``--murano-repo-url`` or with the
corresponding ``MURANO_REPO_URL`` environment variable. After doing so,
running::

    murano --murano-repo-url="http://example.com/" package-import io.app.foo

would access specified repository and download app ``io.app.foo`` from it's
app directory. This option supports an optional ``--version`` parameter, that
would instruct murano client to download package of a specific version.

``package-import`` inspects package requirements specified in the package's
manifest under `Require` section and attempts to import them from
Murano Repository.
``package-import`` also inspects any image prerequisites, mentioned in the
`images.lst` file in the package. If there are any image requirements client
would inspect images already present in the image database. Unless image with
the specific name and hash is present client would attempt to download it.

For more info about specifiying images and requirements for the package see
package creation docs: :ref:`app_pkg`.

If any of the packages, being installed is already registerd in Murano, client
would ask you what do do with it. You can specify the default action with
``--exists-action``, passing `s` for skip, `u` for update, and `a` for abort.

Importing bundles of packages in Murano
=======================================

``package-import`` subcommand can install packages in several different ways:
    * from a locall file
    * from a http url
    * from murano app repository

When creating a package you can specify it's categories with
``-c/--categories`` and set it's publicity with ``--public``

To import a local bundle run::

    murano bundle-import /path/to/bundle

To import a bundle from http url run::

    murano bundle-import http://example.com/path/to/bundle

To import a bundle from murano repository run::

    murano bundle-import bundle_name

Note: When importing from a local file packages would first be searched in a
directory, relative to the directory containing the bundle file itself. This
is done to facilitate installing bundles in an environment with no access to
the repository itself.

Deleting packages from murano
=============================

To delete a package run::

    murano package-delete <PKG_ID>


Downloading package file
========================

Running::

    murano package-download <PKG_ID> > file.zip

would download the zip arhive with specified package

Creating a package
==================

Murano client is able to create application packages from package source
files/directories. To find out more about this command run::

    murano help package-create

This command is useful, when application package files are spread across
several directories, and for auto-generating packages from heat templates
For more info about package composition please see package creation docs:
:ref:`app_pkg`.


Managing Environments
=====================

It is possible to create/update/delete environments with following commands::

   murano environment-create <NAME>
   murano environment-delete <NAME_OR_ID>
   murano environment-list
   murano environment-rename <OLD_NAME_OR_ID> <NEW_NAME>
   murano environment-show <NAME_OR_ID>

You can get list of deployments for environmet with::

   murano deployment-list <NAME_OR_ID>

Managing Categories
===================

It is possible to create/update/delete categories with following commands::

   murano category-create <NAME>
   murano category-delete <ID> [<ID> ...]
   murano category-list
   murano category-show <ID>

Managing Environmet Templates
=============================

It is possible to manage environment templates with following commands::

   murano env-template-create <NAME>
   murano env-template-add-app <NAME> <FILE>
   murano env-template-del-app <NAME> <FILE>
   murano env-template-delete <ID>
   murano env-template-list
   murano env-template-show <ID>
   murano env-template-update <ID> <NEW_NAME>
