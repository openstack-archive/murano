.. _faq:

===
FAQ
===

**There are too many files in Murano package, why not to use a single
Heat Template?**

  To install a simple Apache service to a new VM, Heat Template is
  definitely simpler. But the Apache service is useless without its
  applications running under it. Thus, a new Heat Template is necessary
  for every application that you want to run with Apache. In Murano,
  you can compose a result software to install it on a VM on-the-fly:
  it is possible to select an application that can run under Apache
  dynamically. Or you can set a VM where Apache is installed as a
  parameter. This way, the files in the application package allow
  to compose compound applications with multiple configuration options.
  For any single combination you need a separate Heat Template.

**The Application section is defined in the UI form. Can I remove it?**

  No. The ``Application`` section is a template for Murano object model
  which is the instruction that helps you to understand the
  environment structure that you deploy. While filling the forms that
  are auto-generated from the UI.yaml file, object model is
  updated with the values entered by the user. Eventually, the Murano
  engine receives the resulted object model (.json file) after the
  environment is sent to the deploy.

**The Templates section is defined in the UI form. What's the purpose?**

  Sometimes, the user needs to create several instances with the same
  configuration. A template defined by a variable in the
  ``Templates`` section is multiplied by the value of the number of
  instances that are set by the user. A YAQL ``repeat`` function is
  used for this operation.

**Some properties have Usage, others do not. What does this affect?**

  ``Usage`` indicates how a particular property is used. The default
  value is ``In``, so sometimes it is omitted. The ``Out`` property
  indicates that it is not set from outside, but is calculated in
  the class methods and is available for the ``read`` operation from
  other classes. If you don't want to initialize in the class
  constructor, and the property has no default value, you specify
  ``Out`` in the ``Usage``.

**Can I use multiple inheritance in my classes?**

  Yes. You can specify a list of parent classes instead of a single
  string in the regular YAML notation. The list with one element is
  also acceptable.

**There are FullName and Name properties in the manifest file. What's
the difference between them?**

  ``Name`` is displayed in the web UI catalog, and ``FullName`` is a
  system name used by the engine to get the class definition and
  resolve the class interconnections.

**How does Murano know which class is the main one?**

  There is no ``main`` class term in the MuranoPL. Everything depends
  on a particular object model and an instance class representing the
  instance. Usually, an entry-point class has exactly the same name
  as the package FullName, and it uses other classes.

**What is the difference between $variable and $.variable in the class
definitions?**

  By default, ``$`` represents a current object (similar to ``self``
  in Python or ``this`` in C++/Java/C#), so ``$.variable`` accesses
  the object field/property. In contrast, ``$variable`` (without a dot)
  means a local method variable. Note that ``$`` can change its value
  during execution of some YAQL functions like select, where it means
  a current value. A more safe form is to use a reserved variable
  ``$this`` instead of ``$``. ``$this.variable`` always refers to an
  object-level value in any context.
