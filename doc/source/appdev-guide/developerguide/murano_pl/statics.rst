.. _static_methods_and_properties:

Static methods and properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In MuranoPL, static denotes class methods and class properties (as opposed to
instance methods and instance properties). These methods and properties can be
accessed without an instance present.

Static methods are often used for helper methods that are not bound to any object
(that is, do not maintain a state) or as a convenient way to write a class factory.

Type objects
------------

Usually static methods and properties are accessed using `type object`. That
is, an object that represents the class rather than class instance.

For any given class `foo.Bar` its type object may be retrieved using
any of the following ways:

* Using ``ns:Bar`` notation considering that `ns` is declared in `Namespaces`
  section (and it is `foo` in this case),
* Using ``:Bar`` syntax if `Bar` is in the current namespace (that is, what
  ``=:Bar`` would mean if ``=`` was a valid namespace prefix),
* Using ``type()`` function with a fully qualified class name: ``type('foo.Bar')``,
* By obtaining a type of class instance: ``type($object)`` (available for
  packages with format version starting from `1.3`),
* Through reflection: ``typeinfo($object).type``.

No matter what method was used to get type object, the returned object will
be the same because there can be only one type object per class.

All functions that accept type name, for example ``new()`` function, also
accept type objects.


Accessing static methods and properties
---------------------------------------

Static methods can be invoked using one of the two ways:

 * Using `type object`: ``ns:Bar.foo(arg)``, ``:Bar.foo(arg)``, and so on,
 * On a class instance similar to normal methods: ``$obj.foo(arg)``.

Access to properties is similar to that:
 * Using `type object`: ``ns:Bar.property``, ``:Bar.property``, and so on,
 * On a class instance: ``$obj.property``.

Static properties are defined on a class rather than on an instance.
Therefore, their values will be the same for all class instances (for
particular version of the class).


Declaration of static methods and properties
--------------------------------------------

Methods and properties are declared to be static by specifying
``Usage: Static`` on them.

For example:

.. code-block:: yaml

   Properties:
     property:
       Contract: $.string()
       Usage: Static

   Methods:
     foo:
       Usage: Static
       Body:
       - Return: $.property

Static properties are never initialized from object model but can be modified
from within MuranoPL code (i.e. they are not immutable).
Static methods also can be executed as an action from outside using
``Scope: Public``. Within static method `Body` ``$this`` (and ``$`` if not
set to something else in expression) are set to type object rather than to
instance, as it is for regular methods.


Static methods written in Python
--------------------------------

For MuranoPL classes entirely or partially written in Python, all methods
that have either ``@staticmethod`` or ``@classmethod`` decorators are
automatically imported as static methods and work as they normally do in
Python.


.. _extension_methods:

Extension methods
~~~~~~~~~~~~~~~~~

Extension methods are a special kind of static methods that can act as if they
were regular instance methods of some other type.

Extension methods enable you to "add" methods to existing types without
modifying the original type.


Defining extension methods
--------------------------

Extension methods are declared with the ``Usage: Extension`` modifier.

For example:

.. code-block:: yaml

   Name: SampleClass
   Methods:
     mul:
       Usage: Extension
       Arguments:
       - self:
           Contract: $.int().notNull()
       - arg:
           Contract: $.int().notNull()
       Body:
         Return: $self * $arg

Extension method are said to extend some other type and that type is deducted
from the first method argument contract. Thus extension methods must have
at least one argument.

Extension methods can also be written in Python just the same way as static
methods. However one should be careful in method declaration and use precise
YAQL specification of the type of first method argument otherwise the method
will become an extension of any type.

To turn Python static method into extension method it must be decorated with
``@yaql.language.specs.meta('Usage', 'Extension')`` decorator.


Using extension methods
-----------------------

The example above defines a method that extends integer type. Therefore, with
the method above it becomes possible to say ``2.mul(3)``. However, the most
often usage is to extend some existing MuranoPL class using ``class()``
contract.

If the first argument contract does not have ``notNull()``, then the method
can be invoked on the ``null`` object as well (like ``null.foo()``).

Extension methods are static methods and, therefore,can be invoked in a usual
way on type object: ``:SampleClass.mul(2, 3)``. However, unlike regular static
methods extensions cannot be invoked on a class instance because this can
result in ambiguity.


Using extension lookup order
----------------------------

When somewhere in the code the ``$foo.bar()`` expression is encountered, MuranoPL
uses the following order to locate bar() ``implementation``:

* If there is an instance or static method in ``$foo``'s class, it will be used.
* Otherwise if the current class (where this expression was encountered) has
  an extension method called ``bar`` and ``$foo`` satisfies the contract of
  its first argument, then this method will be called.

Normally, if no method was found an exception will be raised. However,
additional extension methods can be imported into the current context. This is
done using the ``Import`` keyword on a class level. The ``Import`` section
specifies either a list or a single type name (or type object) which extension
methods will be available anywhere within the class code:

.. code-block:: yaml

   Name: MyClass
   Import:
   - ns:SomeOtherType
   - :ClassFomCurrentContext
   - 'io.murano.foo.Bar'

If no method was found with the algorithm above, the search continues on
extension methods of all classes listed in the ``Import`` section in the order
types are listed.
