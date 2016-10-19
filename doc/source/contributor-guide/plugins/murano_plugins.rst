.. _muranopl_extensions:

MuranoPL extension plug-ins
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Murano plug-ins allow extending MuranoPL with new classes. Therefore, using
such plug-ins applications with MuranoPL format, you access some additional
functionality defined in a plug-in. For example, the Magnum plug-in, which
allows murano to deploy applications such as Kubernetes using the capabilities
of the Magnum client.

MuranoPL extension plug-ins can be used for the following purposes:

* Providing interaction with external services.

  For example, you want to interact with the OpenStack Image service to get
  information about images suitable for deployment. A plug-in may request image
  data from glance during deployment, performing any necessary checks.

* Enabling connections between murano applications and external hardware

  For example, you have an external load balancer located on a powerful
  hardware and you want your applications launched in OpenStack to use that
  load balancer. You can write a plug-in that interacts with the load balancer
  API. Once done, add new apps to the pool of your load balancer or make any
  other configurations from within your application definition.

* Extending Core Library class functionality, which is responsible for creating
  networks, interaction with murano-agent, and others

  For example, you want to create networks with special parameters for all of
  your applications. You can just copy the class that is responsible for
  network management from the Murano Core library, make the desired
  modification, and load the new class as a plug-in. Both classes will be
  available, and it is up to you to decide which way to create your networks.

* Optimization of frequently used operations. Plug-in classes are written in
  Python, therefore, the opportunity for improvement is significant.

  Murano provides a number of optimization opportunities depending on the
  improvement needs. For example, classes in the Murano Core Library can be
  rewritten in C and used from Python code to improve their performance in
  particular use cases.

.. _package_type_plugins:

MuranoPL package type plug-ins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The only package type natively supported by Murano is MuranoPL. However, it is
possible to extend Murano with support for other formats of application
definitions. TOSCA CSARs and HOT templates are the two examples of alternate
ways to define applications.

Package types plug-ins are normal Python packages that can be distributed
through PyPI and installed using :command:`pip` or its alternatives. It is
important that the plug-in be installed to the same Python instance that is
used to run Murano API and Murano Engine. For multi-node Murano deployments,
plug-ins need to be installed on each node.

To associate a plug-in with a particular package format, it needs to have a
special record in `[entry_points]` section of setup.cfg file:

.. code-block:: ini

   io.murano.plugins.packages =
       Name/Version = namespace:Class

For example:

.. code-block:: ini

   [entry_points]
   io.murano.plugins.packages =
       Cloudify.TOSCA/1.0 = murano_cloudify_plugin.cloudify_tosca_package:CloudifyToscaPackage


This declaration maps particular pair of format-name/version to Python class
that implements Package API interface for the package type. It is possible
to specify several different format names or versions and map them to single
or different Python classes. For example, it is possible to specify

.. code-block:: ini

   [entry_points]
   io.murano.plugins.packages =
       Cloudify.TOSCA/1.0 = murano_cloudify_plugin.cloudify_tosca_package:CloudifyToscaPackage
       Cloudify.TOSCA/1.1 = murano_cloudify_plugin.cloudify_tosca_package:CloudifyToscaPackage
       Cloudify.TOSCA/2.0 = murano_cloudify_plugin.cloudify_tosca_package:CloudifyToscaPackage_v2

.. note::

   A single Python plug-in package may contain several Murano plug-ins
   including of different types. For example, it is possible to combine
   MuranoPL extension and package type plug-ins into a single package.


Tooling for package preparation
-------------------------------

Some package formats may require additional tooling to prepare package ZIP
archive of desired structure. In such cases it is expected that those tools
will be provided by plug-in authors either as part of the same Python package
(by exposing additional shell entry points) or as a separate package or
distribution.

The only two exceptions to this rule are native MuranoPL packages and HOT
packages that are built into Murano (there is no need to install additional
plug-ins for them). Tooling for those two formats is a part of
python-muranoclient.


Package API interface reference
-------------------------------

Plug-ins expose API for the rest of Murano to interact with the package
by implementing `murano.packages.package.Package` interface.


Class initializer:

    `def __init__(self, format_name, runtime_version, source_directory, manifest):`


    * **format_name**: name part of the format identifier (string)
    * **runtime_version**: version part of the format identifier (instance of
      semantic_version.Version)
    * **source_directory**: path to the directory where package content was
      extracted (string)
    * **manifest**: contents of the manifest file (string->string dictionary)

    **Note**: implementations must call base class (`Package`) initializer
    passing the first three of these arguments.

Abstract properties that must be implemented by the plug-in:

    `def full_name(self):`

    * Fully qualified name of the package. Must be unique within package
      scope of visibility (string)

    `def version(self):`

    * Package version (not to confuse with format version!). An instance of
      `semantic_version.Version`

    `def classes(self):`

    * List (or tuple) of MuranoPL class names (FQNs) that package contains

    `def requirements(self):`

    * Dictionary of requirements (dependencies on other packages) in a form
      of key-value mapping from required package FQN string to SemVer
      version range specifier (instance of semantic_version.Spec or string
      representation supported by Murano versioning scheme)

    `def package_type(self):`

    * Package type: "Application" or "Library"

    `def display_name(self):`

    * Human-readable name of the package as presented to the user (string)

    `def description(self):`

    * Package description (string or None)

    `def author(self):`

    * Package author (string or None)

    `def supplier(self):`

    * Package supplier (string or None)

    `def tags(self):`

    * List or tags for the package (list of strings)

    `def logo(self):`

    * Package (application) logo file content (str or None)

    `def supplier_logo(self):`

    * Package (application) supplier logo file content (str or None)

    `def ui(self):`

    * YAML-encoded string containing application's form definition (string or
      None)

Abstract methods that must be implemented by the plug-in:

    `def get_class(self, name):`

    * Returns string containing MuranoPL code (YAML-encoded string) for the
      class whose fully qualified name is in "name" parameter (string)

    `def get_resource(self, name):`

    * Returns path for resource file whose name is in "name" parameter (string)


Properties that can be overridden in the plug-in:

    `def format_name(self):`

    * Canonical format name for the plug-in. Usually the same value that was
      passed to class initializer


    `def runtime_version(self):`

    * Format version. Usually the same value that was passed to class
      initializer (semantic_version.Version)

    `def blob(self):`

    * Package file (.zip) content (str)


PackageBase class
-----------------

Usually, there is no need to manually implement all the methods and properties
described. There is a `murano.packages.package.PackageBase` class that provides
typical implementation of most of required properties by obtaining
corresponding value from manifest file.

When inheriting from PackageBase class, plug-in remains responsible for
implementation of:

* `ui` property
* `classes` property
* `get_class` method

This allows plug-in developers to concentrate on dynamic aspects of the package
type plug-in while keeping all static aspects (descriptions, logos and so on)
consistent across all package types (at least those who inherit from
`PackageBase`).