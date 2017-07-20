.. _manage_plugins:

Creating a Murano plug-in
-------------------------

Murano plug-in is a setuptools-compliant python package with ``setup.py`` and
all other necessary files. For more information about defining stevedore
plug-ins, see `stevedore documentation
<https://docs.openstack.org/stevedore/latest/>`_.

The structure of the demo application package
+++++++++++++++++++++++++++++++++++++++++++++

The package must meet the following requirements:

* It must be a ZIP archive.
* The root folder of the archive must contain a ``manifest.yaml`` file.
* The manifest must be a valid YAML file representing key-value associative
  array.
* The manifest should contain a *Format* key, that is, a format identifier. If
  it is not present, "MuranoPL/1.0" is used.

Murano uses the *Format* attribute of the manifest file to find an appropriate
plug-in for a particular package type. All interactions between the rest of
Murano and package file contents are done through the plug-in interface alone.

Because Murano never directly accesses files inside the packages, it is
possible for plug-ins to dynamically generate MuranoPL classes on the fly.
Those classes will be served as adapters between Murano and third-party systems
responsible for deployment of particular package types. Thus, for Murano all
packages remain to be of MuranoPL type though some of them are "virtual".

The format identifier has the following format: ``Name/Version``.
For example, ``Heat.HOT/1.0``. If name is not present, it is assumed to be
``MuranoPL`` (thus ``1.0`` becomes ``MuranoPL/1.0``). Version strings are in
SemVer three-component format (major.minor.patch). Missing version components
are assumed to be zero (thus 1.0 becomes 1.0.0).

Installing a plug-in
--------------------

To use a plug-in, install it on murano nodes in the same Python environment
with murano engine service.

To install a plug-in:

#. Execute the plug-in setup script.

   Alternatively, use a package deployment tool, such as pip:

   .. code-block:: console

      cd plugin_dir
      pip install .

#. Restart murano engine. After that, it will be possible to upload and deploy
   the applications that use the capabilities that a plug-in provides.

Plug-in versioning
------------------

Plug-ins located in Murano repository have the same version as Murano.
Therefore, to use a specific version of such plug-in, checkout to this version.
Then specify the version of plug-in classes in your application's manifest file
as usual:

   .. code-block:: yaml

       Require:
         murano.plugins.example: 2.0.0

It should be standard SemVer format version string consisting of three parts:
Major.Minor.Patch. For more information about versioning, refer to
:ref:`versioning`.

.. note::
   Enable Glare to use versioning.

Organization
------------

Documentation
+++++++++++++

Documentation helps users understand what your plug-in does. For plug-ins
located in the Murano repository, create a ``README.rst`` file in the main
folder of the plug-in. The ``README.rst`` file may contain information about
the plug-in and an installation guide.

Code
++++

The code of your plug-in may be located in the following repositories:

* Murano repository. In this case, the plug-in should be located in the
  ``murano/contrib/plugins`` folder.

* A separate repository. In this case, create your own project.

Bugs
++++

All bugs for specific plug-ins are reported in their projects. Bugs related
to plug-ins located in Murano repository should be reported in the `Murano
<https://bugs.launchpad.net/murano/>`_ project.
