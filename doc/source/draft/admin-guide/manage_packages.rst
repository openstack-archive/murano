.. _manage-packages:

.. toctree::
   :maxdepth: 1:

=================
Managing packages
=================

Managing packages on engine-side
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get access to contents of murano packages ``murano-engine`` queries
``murano-api``. However it also possible to specify a list of directories,
that may contain packages locally. This option is useful to speed-up
debugging and development of packages and/or to save bandwidth between api
and engine. If local directories are specified — they're examined before
querying the API.

Local package directories
-------------------------

To define a list of directories where the engine would look for package files
you should set ``load_packages_from`` option in ``packages_opts`` section
inside :file:`murano.conf` config file. This option can be set to a
(comma-separated) list of directory paths. Whenever an engine needs to access a
package it would inspect these directories first, before accessing
``murano-api``.

API package cache
-----------------

If the package was not found in any of the ``load_packages_from`` directories
(or if none were specified), then ``murano-engine`` queries API for package
contents.
Whenever ``murano-engine`` downloads a package from API it stores and unpacks
it locally. Engine uses directory defined in ``packages_cache`` option in
``packages_opts`` section inside :file:`murano.conf` config file. If it is not
used a temporary directory is created.

``enable_packages_cache`` option in the same section defines whether the
packages would persist on disk or not. When set to ``False`` each package,
downloaded from API would be stored in a separate directory, that would be
deleted after the deployment (or action) is over. This means, that every
deployment (or action execution) would need to download all the packages
it requires, regardless of any packages downloaded previously by the engine.
When set to ``True`` (default) the engine would share downloaded packages
between deployments (and action executions). This means, that packages would
persist on disk and would have to be eventually deleted. This is done
optimistically: whenever engine requires a package and that package is not in
found locally — the engine would download the package. Afterwards it would
check all the previously cached packages with the same FQN and same version
if the cached package is not required by any ongoing deployment
it get's deleted. Otherwise it stays on disk until a new version is downloaded.

.. note::
   On Unix-based Operating Systems murano uses fcntl for IPC locks, that
   support both shared and exclusive locking. On Windows msvcrt is used.
   It doesn't support shared file locks, therefore enabling package cache
   mechanism under windows might result in decrease of performance, since only
   one process would be able to use a package at the same time.
