.. _metadata:

MuranoPL Metadata
~~~~~~~~~~~~~~~~~

MuranoPL metadata is a way to attach additional information to various MuranoPL
entities such as classes, packages, properties, methods, and method arguments.
That information can be used by both applications (to implement dynamic
programming techniques) or by the external callers (API consumers like UI or
even by the Murano Engine itself to impose some runtime behavior based on
well known meta values). Thus, metadata is a flexible alternative to adding new
keyword for every new feature.

Work with metadata includes the following cases:

* Defining your own metadata classes
* Attaching metadata to various parts of MuranoPL code
* Obtaining metadata and its usage

Define metadata classes
-----------------------

Define MuranoPL class with the description of arbitrary metadata. The class
that can be used as metadata differs from the regular class:

* The ``Usage`` attribute of the former equals to ``Meta``, while the ``Usage``
  attribute of the latter equals to ``Class``. The default value of the
  ``Usage`` attribute is ``Class``.

* Metadata class has additional attributes (``Cardinality``, ``Applies`` and
  ``Inherited``) to control how and where instances of that class can be
  attached.

Cardinality
+++++++++++

The ``Cardinality`` attribute can be set to either ``One`` or ``Many`` and
indicates the possibility to attach two or more instances of metadata to a
single language entity. The default value is ``One``.

Applies
+++++++

The ``Applies`` attribute can be set to one of ``Package``, ``Type``,
``Method``, ``Property``, ``Argument`` or ``All`` and controls the possible
language entities which instances of metadata class can be attached to. It is
possible to specify several values using YAML list notation. The default value
is ``All``.

Inherited
+++++++++

The ``Inherited`` attribute can be set to ``true`` or ``false`` and specifies
if there is metadata retained for child classes, overridden methods and
properties. The default value is ``false``.

Using of ``Inherited: true`` has the following consequences.

If some class inherits from two classes with the same metadata attached and
this metadata has ``Cardinality: One``, it will lead to emerging of two
metadata objects with ``Cardinality: One`` within a single entity and will
throw an exception. However, if the child class has this metadata attached
explicitly, it will override the inherited metas and there is no conflict.

If the child class has the same meta as its parent (attached explicitly),
then in case of ``Cardinatity: One`` the meta of the child overrides the
meta of the parent as it is mentioned above. And in case of
``Cardinatity: Many`` meta of the parent is added to the list of the child's
metas.

Example
+++++++

The following example shows a simple meta-class implementation:

.. code-block:: yaml

    Name: MetaClassOne
    Usage: Meta
    Cardinality: One
    Applies: All

    Properties:
      description:
        Contract: $.string()
        Default: null

      count:
        Contract: $.int().check($ >= 0)
        Default: 0

``MetaClassOne`` is defined as a metadata class by setting the ``Usage``
attribute to ``Meta``. The ``Cardinality`` and ``Applies`` attributes determine
that only one instance of ``MetaClassOne`` can be attached to object of any
type. The ``Inherited`` attribute is omitted so there is no metadata
retained for child classes, overridden methods and properties. In the
example above, ``Cardinality`` and ``Applies`` can be omitted as well, as
their values are set to default but in this case the author wants to be
explicit.

The following example shows metadata class with different values of attributes:

.. code-block:: yaml

    Name: MetaClassMany
    Usage: Meta
    Cardinality: Many
    Applies: [Property, Method]
    Inherited: true

    Properties:
      description:
        Contract: $.string()
        Default: null

      count:
        Contract: $.int().check($ >= 0)
        Default: 0

An instance (or several instances) of ``MetaClassMany`` can be attached to
either property or method. Overridden methods and properties inherit
metadata from its parents.

Attach metadata to a MuranoPL entity
------------------------------------

To attach metadata to MuranoPL class, package, property, method or method
argument, add the ``Meta`` keyword to its description. Under the
description, specify a list of metadata class instances which you want to
attach to the entity. To attach only one metadata class instance, use a single
scalar instead of a list.

Consider the example of attaching previously defined metadata to different
entities in a class definition:

.. code-block:: yaml

    Namespaces:
      =: io.murano.bar
      std: io.murano
      res: io.murano.resources
      sys: io.murano.system


    Name: Bar

    Extends: std:Application

    Meta:
      MetaClassOne:
        description: "Just an empty application class with some metadata"
        count: 1

    Properties:
      name:
        Contract: $.string().notNull()
        Meta:
          - MetaClassOne:
              description: "Name of the app"
              count: 1
          - MetaClassMany:
              count: 2
          - MetaClassMany:
              count: 3

    Methods:
      initialize:
        Body:
          - $._environment: $.find(std:Environment).require()
        Meta:
          MetaClassOne:
            description: "Method for initializing app"
            count: 1

      deploy:
        Body:
          - If: not $.getAttr(deployed, false)
            Then:
              - $._environment.reporter.report($this, 'Deploy started')
              - $._environment.reporter.report($this, 'Deploy finished')
              - $.setAttr(deployed, true)

The ``Bar`` class has an instance of metadata class ``MetaClassOne`` attached.
For this, the ``Meta`` keyword is added to the ``Bar`` class description and
the instance of the ``MetaClassOne`` class is specified under it. This
instance's properties are ``description`` and ``count``.

There are three meta-objects attached to the ``name`` property of the ``Bar``
class. One of it is a ``MetaclassOne`` object and the other two are
``MetaClassMany`` objects. There can be more than one instance of
``MetaClassMany`` attached to a single entity since the ``Cardinality``
attribute of ``MetaClassMany`` is set to ``Many``.

The ``initialize`` method of ``Bar`` also has its metadata.

To attach metadata to the package, add the ``Meta`` keyword to
``manifest.yaml`` file.

Example:

.. code-block:: yaml

    Format: 1.0
    Type: Application
    FullName: io.murano.bar.Bar
    Name: Bar
    Description: |
        Empty Description
    Author: author
    Tags: [bar]
    Classes:
        io.murano.bar.Bar: Bar.yaml
        io.murano.bar.MetaClassOne: MetaClassOne.yaml
        io.murano.bar.MetaClassMany: MetaClassMany.yaml
    Supplier:
     Name: Name
     Description: Description
     Summary: Summary
    Meta:
     io.murano.bar.MetaClassOne:
       description: "Just an empty application with some metadata"
       count: 1

Obtain metadata in runtime
--------------------------

Metadata can be accessed from MuranoPL using reflection capabilities and
from Python code using existing YAQL mechanism.

The following example shows how applications can access attached metadata:

.. code-block:: yaml

    Namespaces:
      =: io.murano.bar
      std: io.murano
      res: io.murano.resources
      sys: io.murano.system

    Name: Bar

    Extends: std:Application

    Meta:
      MetaClassOne:
        description: "Just an empty application class with some metadata"

    Methods:
      sampleAction:
        Scope: Public
        Body:
          - $._environment.reporter.report($this, typeinfo($).meta.
              where($ is MetaClassOne).single().description)

The ``sampleAction`` method is added to the ``Bar`` class definition. This
makes use of metadata attached to the ``Bar`` class.

The information about the ``Bar`` class is received by calling the
``typeinfo`` function. Then metadata is accessed through the ``meta``
property which returns the collection of all meta attached to the property.
Then it is checked that the meta is a ``MetaClassOne`` object to ensure that
it has ``description``. While executing the action, the phrase "Just an
empty application class with some metadata" is reported to a log. Some
advanced usages of MuranoPL reflection capabilities can be found in the
corresponding section of this reference.

By using metadata, an application can get information of any type attached
to any object and use this information to change its own behavior. The most
valuable use-cases of metadata can be:

* Providing information about capabilities of application and its parts
* Setting application requirements

Capabilities can include version of software, information for use in UI or
CLI, permissions, and any other. Metadata can also be used in requirements as
a part of the contract.

The following example demonstrates the possible use cases for the metadata:

.. code-block:: yaml

    Name: BlogApp

    Meta:
      m:SomeFeatureSupport:
        support: true

    Properties:
      volumeName:
        Contract: $.string().notNull()
        Meta:
          m:Deprecated:
            text: "volumeName property is deprecated"
      server:
        Contract: $.class(srv:CoolServer).notNull().check(typeinfo($).meta.
                   where($ is m:SomeFeatureSupport and $.support = true).any())

    Methods:
      importantAction:
        Scope: Public
        Meta:
          m:CallerMustBeAdmin

Note, that the classes in the example do not exist as of Murano Mitaka, and
therefore the example is not a real working code.

The ``SomeFeatureSupport`` metadata with ``support: true`` says that the
``BlogApp`` application supports some feature. The ``Deprecated`` metadata
attached to the ``volumeName`` property informs that this
property has a better alternative and it will not be used in the future
versions anymore. The ``CallerMustBeAdmin`` metadata attached to the
``importantAction`` method sets permission to execute this method to the
admin users only.

In the contract of the ``server`` property it is specified that the server
application must be of the ``srv:CoolServer`` class and must have the
attached meta-object of the ``m:SomeFeatureSupport`` class with the
``support`` property set to ``true``.
