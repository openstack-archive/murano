.. _manage-packages:

=================
Managing packages
=================

Managing packages on engine side
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get access to the contents of murano packages, ``murano-engine`` queries
``murano-api``. However, it is also possible to specify a list of directories
that may contain packages locally. This option is useful to speed up
debugging and development of packages and/or to save bandwidth between the API
and the engine. If local directories are specified, they are examined before
querying the API.

Local package directories
-------------------------

To define a list of directories where the engine would look for package files,
set the ``load_packages_from`` option in the ``engine`` section
of the :file:`murano.conf` configuration file. This option can be set to a
comma-separated list of directory paths. Whenever an engine needs to access a
package, it would inspect these directories first, before accessing
``murano-api``.

API package cache
-----------------

If the package was not found in any of the ``load_packages_from`` directories,
or if none were specified, then ``murano-engine`` queries API for package
contents.
Whenever ``murano-engine`` downloads a package from API, it stores and unpacks
it locally. The engine uses the directory defined in the ``packages_cache``
option in the ``engine`` section of the :file:`murano.conf`
configuration file. If it is not used, a temporary directory is created.

The ``enable_packages_cache`` option in the same section defines whether the
packages would persist on disk or not. When set to ``False``, each package
downloaded from API is stored in a separate directory, that will be deleted
after the deployment (or action) is over. This means that every deployment
or action execution needs to download all the packages it requires,
regardless of any packages previously downloaded by the engine. When set to
``True`` (default), the engine shares downloaded packages between deployments
and action executions. This means that packages persist on disk and have to be
eventually deleted. Therefore, whenever the engine requires a package and that
package is not found locally, the engine downloads the package. Afterwards, it
checks all the previously cached packages with the same FQN and same version.
If the cached package is not required by any ongoing deployment, it gets
deleted. Otherwise, it stays on disk until a new version is downloaded.

.. note::
   On UNIX-based operating systems, murano uses ``fcntl`` for IPC locks that
   support both shared and exclusive locking. On Windows, ``msvcrt`` is used.
   It does not support shared file locks. Therefore, enabling package cache
   mechanism under Windows might result in performance decrease, since only
   one process would be able to use one package at the same time.
