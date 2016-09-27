.. _versioning:

Versioning
~~~~~~~~~~

Versioning is an ability to assign a version number to some particular package
(and, in turn, to a class) and then distinguish packages with different
versions.

Package version
---------------

It is possible to specify a version for packages. You can import several
versions of the same package simultaneously and even deploy them inside a
single environment. To do this, you should use Glare as a storage for packages.
But if you're going to keep only the latest version API is still good enough
and both FormatVersion and Version rules will still be there. For more
information about using Glare, refer to :ref:`glare_usage`.

To specify the version of your package, add a new section to the manifest file:

  .. code-block:: yaml

   Version: 0.1.0

  ..

It should be standard SemVer format version string consisting of 3 parts:
``Major.Minor.Patch`` and optional SemVer suffixes
``[-dev-build.label[+metadata.label]]``.
All MuranoPL classes have the version of the package they are contained in.
If no version is specified, the package version is *0.0.0*.

.. note::
   It is impossible to show multiple versions of the same application in murano
   dashboard: only the last one is shown if the multiple versions are present.

Package requirements
--------------------

In some cases, packages may require other packages for their work.
You need to list such packages in the `Require` section of the manifest
file:

  .. code-block:: yaml

   Require:
     package1_FQN: version_spec_1
     ...
     packageN_FQN: version_spec_N

  ..

``version_spec`` here denotes the allowed version range. It can be either in
semantic_version specification pip-like format or as a partial version string.
If you do not want to specify the package version, leave this value empty:

  .. code-block:: yaml

   Require:
     package1_FQN: '>=0.0.3'
     package2_FQN:

  ..

In this case, version specification is equal to *0*.


.. note::
   All packages depend on the `io.murano` package (Core Library). If you do not
   specify this requirement in the list (or the list is empty, or there is
   no ``Require`` key in the package manifest), then dependency *io.murano: 0*
   will be automatically added.


Object version
--------------

You can specify the version of the objects in UI definition when your
application requires a specific version of some class. To do this, add a new key
``classVersion`` to section ``?`` describing the object:

  .. code-block:: yaml

   ?:
     type: io.test.apps.TestApp
     classVersion: version_spec

  ..


Side-by-side versioning of packages
-----------------------------------

In some cases it might happen that several different versions of the same class
are simultaneously present in a single environment:

 * There are different versions of the same MuranoPL class inside a single
   object model (environment).
 * Several class versions encounter within class parents. For example, class A
   extends B and C and class C inherits B2, where B and B2 are two different
   versions of the same class.

The first case, when two different versions of the same class need to communicate
with each other, is handled by the fact that in order to do that there is a
``class()`` contract for that value. ``class()`` contract validates object
version against package requirements. If class A has a property with contract
$.class(B), then an object passed in this property when upcasted to B must have a
version compatible with requirement specification in A's package (requesting
B's package).

For the second case, where a single class attempts to inherit from two
different versions of the same class engine (DSL), it attempts to find a
version of this class which satisfies all parties and use it instead.
However, if it is impossible, all remained different versions of the same class
are treated as if they are unrelated classes.

For example: classA inherits classB from packageX and classC from packageY.
Both classB and classC inherit from classD from packageZ; however, packageX
depends on the version 1.2.0 of packageZ, while packageY depends on the
version 1.3.0. This leads to a situation when classA transitively inherits
classD of both versions 1.2 and 1.3. Therefore, an exception is thrown.
However, if packageY's dependency would be just "1" (which means any of the
1.x.x family), the conflict would be resolved and the 1.2 would be used as it
satisfies both inheritance chains.

Murano engine is free to use any package version that is valid for the spec.
For example, one application requires packageX with version spec < 0.3 and
another package with the spec > 0. If both packages are get used in the same
environment and the engine already loaded version 0.3 it can still use it for
the second requirement even if there is a package with version 0.4 in the
catalog and the classes from both classes are never interfere. In other words,
engine always tries to minimize the number of versions in use for
the single package to avoid conflicts and unnecessary package downloads.
However, it also means that packages not always get the latest requirements.

.. _ManifestFormat:

Manifest format versioning
--------------------------

The manifests of packages are versioned using *Format* attribute. Currently,
available versions are: `1.0`, `1.1`, `1.2` and `1.3`.
The versioning of manifest format is directly connected with YAQL and version
of murano itself.

The short description of versions:

==================  ===========================================================
  Format version                             Description
==================  ===========================================================
      **1.0**         supported by all versions of murano. Use this version
                      if you are planning to use *yaql 0.2* in your
                      application

      **1.1**         supported since Liberty. *yaql 0.2* is supported in
                      legacy mode. Specify it, if you want to use features
                      from *yaql 0.2* and *yaql 1.0.0* at the same time in
                      your application.

      **1.2**         supported since Liberty. Do not use *yaql 0.2* in
                      applications with this format.

      **1.3**         supported since Mitaka. *yaql 1.1* is available. It's
                      recommended specifying this format in new applications,
                      where compatibility with older versions of murano is not
                      required.

      **1.4**         supported since Newton. Keyword ``Scope`` is introduced
                      for class methods to declare method's accessibility from
                      outside through the API call.
==================  ===========================================================

UI forms versioning
-------------------

UI forms are versioned using Format attribute inside YAML definition.
For more information, refer to :ref:`corresponding documentation<DynamicUIversion>`.

Execution plan format versioning
--------------------------------

Format of an execution plan can be specified using property ``FormatVersion``.
More information can be found :ref:`here<format_version>`.

