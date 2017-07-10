.. _class_templ:

Common class structure
~~~~~~~~~~~~~~~~~~~~~~

Here is a common template for class declarations. Note, that it is in the YAML
format.

.. code-block:: yaml
   :linenos:

   Name: class name
   Namespaces: namespaces specification
   Extends: [list of parent classes]
   Properties: properties declaration
   Methods:
       methodName:
           Arguments:
               - list
               - of
               - arguments
           Body:
               - list
               - of
               - instructions

Thus MuranoPL class is a YAML dictionary with predefined key names, all keys except
for ``Name`` are optional and can be omitted (but must be valid if specified).

Class name
----------

Class names are alphanumeric names of the classes. Traditionally, all class names
begin with an upper-case letter symbol and are written in PascalCasing.

In MuranoPL all class names are unique. At the same time, MuranoPL
supports namespaces. So, in different namespaces you can have classes
with the same name. You can specify a namespace explicitly, like
`ns:MyName`. If you omit the namespace specification, ``MyName`` is
expanded using the default namespace ``=:``. Therefore, ``MyName``
equals ``=:MyName`` if ``=`` is a valid namespace.

Namespaces
----------

Namespaces declaration specifies prefixes that can be used in the class body
to make long class names shorter.

.. code-block:: yaml

   Namespaces:
       =: io.murano.services.windows
       srv: io.murano.services
       std: io.murano

In the example above, the ``srv: Something`` class name is automatically
translated to ``io.murano.services.Something``.

``=`` means the current namespace, so that ``MyClass`` means
``io.murano.services.windows.MyClass``.

If the class name contains the period (.) in its name, then it is assumed
to be already fully namespace qualified and is not expanded.
Thus ``ns.Myclass`` remains as is.


.. note::
   To make class names globally unique, we recommend specifying a developer's
   domain name as a part of the namespace.

Extends
-------

MuranoPL supports multiple inheritance. If present, the ``Extends`` section
shows base classes that are extended. If the list consists of a single entry,
then you can write it as a scalar string instead of an array. If you
do not specify any parents or omit the key, then the class extends
``io.murano.Object``. Thus, ``io.murano.Object`` is the root class
for all class hierarchies.

.. _class_props:


Properties
----------

Properties are class attributes that together with methods create public
class interface. Usually, but not always, properties are the values, and
reference other objects that have to be entered in an environment
designer prior to a workflow invocation.

Properties have the following declaration format:

.. code-block:: yaml

   propertyName:
       Contract: property contract
       Usage: property usage
       Default: property default

Contract
++++++++

Contract is a YAQL expression that says what type of the value is expected for
the property as well as additional constraints imposed on a property. Using
contracts you can define what value can be assigned to a property or argument.
In case of invalid input data it may be automatically transformed to confirm
to the contract. For example, if bool value is expected and user passes any
not null value it will be converted to ``True``. If converting is impossible
exception ``ContractViolationException`` will be raised.

The following contracts are available:

+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
|  Operation                                                |  Definition                                                                                     |
+===========================================================+=================================================================================================+
| | $.int()                                                 | | an integer value (may be null). String values consisting of digits are converted to integers  |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.int().notNull()                                       | | a mandatory integer                                                                           |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.string()                                              | | a string. If the value is not a string, it is converted to a string                           |
| | $.string().notNull()                                    |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.bool()                                                | | bools are true and false. ``0`` is converted to false, other integers to true                 |
| | $.bool().notNull()                                      |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.class(ns:ClassName)                                   | | value must be a reference to an instance of specified class name                              |
| | $.class(ns:ClassName).notNull()                         |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.template(ns:ClassName)                                | | value must be a dictionary with object-model representation of specified class name           |
| | $.template(ns:ClassName).notNull()                      |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.class(ns:ClassName, ns:DefaultClassName)              | | create instance of the ``ns:DefaultClassName`` class if no instance provided                  |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.class(ns:Name).check($.p = 12)                        | |  the value must be of the ``ns:Name`` type and have the ``p`` property equal to 12            |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.class(ns:Name).owned()                                | |  a current object must be direct or indirect owner of the value                               |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.class(ns:Name).notOwned()                             | |  the value must be owned by any object except current one                                     |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int()]                                               | | an array of integers. Similar to other types.                                                 |
| | [$.int().notNull()]                                     |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int().check($ > 0)]                                  | | an array of the positive integers (thus not null)                                             |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int(), $.string()]                                   | |  an array that has at least two elements, first is int and others are strings                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int(), 2]                                            | | an array of ints with at least 2 items                                                        |
| | [$.int(), 2, 5]                                         | | an array of ints with at least 2 items, and maximum of 5 items                                |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | { A: $.int(), B: [$.string()] }                         | |  the dictionary with the ``A`` key of the int type and ``B`` - an array of strings            |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $                                                       | | any scalar or data structure as is                                                            |
| | []                                                      | | any array                                                                                     |
| | {}                                                      | | any dictionary                                                                                |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | { $.string().notNull(): $.int().notNull() }             | |  dictionary string -> int                                                                     |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | A: StringMap                                            | | the dictionary with the ``A`` key that must be equal to ``StringMap``, and other keys be      |
| | $.string().notNull(): $                                 | | any scalar or data structure                                                                  |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.check($ in $this.myStaticMethod())                    | | the value must be equal to one of a member of a list returned by static method of the class   |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.check($this.myStaticMethod($))                        | | the static method of the class must return true for the value                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+

In the example below property ``port`` must be int value greater than 0 and
less than 65536; ``scope`` must be a string value and one of 'public', 'cloud',
'host' or 'internal', and ``protocol`` must be a string value and either
'TCP' or 'UDP'. When user passes some values to these properties it will be checked
that values confirm to the contracts.

.. code-block:: yaml

    Namespaces:
      =: io.murano.apps.docker
      std: io.murano

    Name: ApplicationPort

    Properties:
      port:
        Contract: $.int().notNull().check($ > 0 and $ < 65536)

      scope:
        Contract: $.string().notNull().check($ in list(public, cloud, host, internal))
        Default: private

      protocol:
        Contract: $.string().notNull().check($ in list(TCP, UDP))
        Default: TCP

    Methods:
      getRepresentation:
        Body:
          Return:
            port: $.port
            scope: $.scope
            protocol: $.protocol


The ``template`` contract does the same validation as the ``class`` contract,
but does not require the actual object to be passed as a property or argument.
Instead it allows to create an object from the given template later. Also you
can exclude some of the properties from validation and provide them later in
the body of the method.

Consider the following example:

.. code-block:: yaml

    Namespaces:
      =: io.murano.applications
      res: io.murano.resources
      std: io.murano

    Name: TemplateServerProvider

    Properties:
      template:
        Contract: $.template(res:Instance, excludeProperties => [name]).notNull()
      serverNamePattern:
        Contract: $.string().notNull()
      threshold:
        Contract: $.int().check($ > 0)

    Methods:
      createReplica:
        Arguments:
          - index:
              Contract: $.int().notNull()
          - owner:
              Contract: $.class(std:Object)
        Body:
          - If: $index < $this.threshold
            Then:
              - $template: $this.template
              - $template.name: $this.serverNamePattern.format($index)
              - $template['?'].name: format('Server {0}', $index)
              - Return: new($template, $owner)
            Else:
              - Return: null

In the example above the class has the ``template`` property that is validated
by the ``template`` contract. It holds the template of the object of the
``Instance`` class or its inheritor. In the ``createReplica`` method
``template`` is used to dynamically create instances in runtime considering
some conditions and customizing the ``name`` property of an instance, as it
was excluded from validation.

You still can pass an actual object to the property or argument with the
``template`` contract, but it will be automatically converted to its object
model representation.

.. _property_usage:

Property usage
++++++++++++++

Usage states the purpose of the property. This implies who and how can
access it. The following usages are available:

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - | Value
     - | Explanation

   * - | In
     - | Input property. Values of such properties are obtained from a user
         and cannot be modified in MuranoPL workflows. This is the default
         value for the Usage key.

   * - | Out
     - | A value is obtained from executing MuranoPL workflow and cannot be
         modified by a user.

   * - | InOut
     - | A value can be modified both by user and by workflow.

   * - | Const
     - | The same as ``In`` but once workflow is executed a property cannot be
         changed neither by a user nor by a workflow.

   * - | Runtime
     - | A property is visible only from within workflows. It is neither read
         from input nor serialized to a workflow output.

   * - | Static
     - | Property is defined on a class rather than on an instance.
         See :ref:`static_methods_and_properties` for details.

   * - | Config
     - | A property allows to have per-class configuration. A value is obtained
         from the config file rather than from the object model. These config
         files are stored in a special folder that is configured in the
         ``[engine]`` section of the Murano config file under the
         ``class_configs`` key.

The usage attribute is optional and can be omitted (which implies ``In``).

If the workflow tries to write to a property that is not declared with
one of the types above, it is considered to be private and accessible
only to that class (and not serialized to output and thus would be
lost upon the next deployment). An attempt to read the property that was
not initialized results in an exception.


Default
+++++++

Default is a value that is used if the property value is not mentioned in
the input object model, but not when it is set to null.
Default, if specified, must conform to a declared property contract.
If Default is not specified, then null is the default.

For properties that are references to other classes, Default can modify
a default value of the referenced objects. For example:

.. code-block:: yaml

  p:
   Contract: $.class(MyClass)
   Default: {a: 12}

This overrides default for the ``a`` property of ``MyClass`` for instance
of ``MyClass`` that is created for this property.

Workflow
--------

Workflows are the methods that describe how the entities that are
represented by MuranoPL classes are deployed.

In a typical scenario, the root object in an input data model is of
the ``io.murano.Environment`` type, and has the ``deploy`` method.
This method invocation causes a series of infrastructure activities
(typically, a Heat stack modification) and the deployment scripts
execution initiated by VM agents commands. The role of the workflow
is to map data from the input object model, or a result of previously
executed actions, to the parameters of these activities and to
initiate these activities in a correct order.


Methods
-------

Methods have input parameters, and can return a value to a caller.
Methods are defined in the Workflow section of the class using the
following template::

  methodName:
      Scope: Public
      Arguments:
         - list
         - of
         - arguments
      Body:
         - list
         - of
         - instructions

Public is an optional parameter that specifies methods to be executed
by direct triggering after deployment.


.. _method_arguments:

Method arguments
++++++++++++++++

Arguments are optional too, and are declared using the same syntax
as class properties. Same as properties, arguments also have contracts and
optional defaults.

Unlike class properties Arguments may have a different set of Usages:

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - | Value
     - | Explanation

   * - | Standard
     - | Regular method argument. Holds a single value based on its contract.
         This is the default value for the Usage key.

   * - | VarArgs
     - | A variable length argument. Method body sees it as a list of values,
         each matching a contract of the argument.

   * - | KwArgs
     - | A keywrod-based argument, Method body sees it as a dict of values,
         with keys being valid keyword strings and values matching a contract
         of the argument.

Arguments example:

.. code-block:: yaml

  scaleRc:
    Arguments:
      - rcName:
          Contract: $.string().notNull()
      - newSize:
          Contract: $.int().notNull()
      - rest:
          Contract: $.int()
          Usage: VarArgs
      - others:
          Contract: $.int()
          Usage: KwArgs

.. method_body:

Method body
+++++++++++

The Method body is an array of instructions that get executed sequentially.
There are 3 types of instructions that can be found in a workflow body:

* Expressions,
* Assignments,
* Block constructs.

.. method_usage:

Method usage
++++++++++++

Usage states the purpose of the method. This implies who and how can
access it. The following usages are available:

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - | Value
     - | Explanation

   * - | Runtime
     - | Normal instance method.

   * - | Static
     - | Static method that does not require class instance.
         See :ref:`static_methods_and_properties` for details.

   * - | Extension
     - | Extension static method that extends some other type.
         See :ref:`extension_methods` for details.

   * - | Action
     - | Method can be invoked from outside (using Murano API).
         This option is deprecated for the package format versions > 1.3 in
         favor of ``Scope: Public`` and occasionally will be no longer
         supported.
         See :ref:`actions` for details.

The ``Usage`` attribute is optional and can be omitted (which implies
``Runtime``).

Method scope
++++++++++++

The ``Scope`` attribute declares method visibility. It can have two possible
values:

* `Session` - regular method that is accessible from anywhere in the current
  execution session. This is the default if the attribute is omitted;

* `Public` - accessible anywhere, both within the session and from
  outside through the API call.

The ``Scope`` attribute is optional and can be omitted (which implies
``Session``).

Expressions
+++++++++++

Expressions are YAQL expressions that are executed for their side effect.
All accessible object methods can be called in the expression using
the ``$obj.methodName(arguments)`` syntax.

+-----------------------------------------+----------------------------------------------------------------+
|  Expression                             |  Explanation                                                   |
+=========================================+================================================================+
| | $.methodName()                        | | invoke method 'methodName' on this (self) object             |
| | $this.methodName()                    |                                                                |
+-----------------------------------------+----------------------------------------------------------------+
| | $.property.methodName()               | | invocation of method on object that is in ``property``       |
| | $this.property.methodName()           |                                                                |
+-----------------------------------------+----------------------------------------------------------------+
| | $.method(1, 2, 3)                     | | methods can have arguments                                   |
+-----------------------------------------+----------------------------------------------------------------+
| | $.method(1, 2, thirdParameter => 3)   | | named parameters also supported                              |
+-----------------------------------------+----------------------------------------------------------------+
| | list($.foo().bar($this.property), $p) | | complex expressions can be constructed                       |
+-----------------------------------------+----------------------------------------------------------------+


Assignment
++++++++++

Assignments are single key dictionaries with a YAQL expression as a key
and arbitrary structure as a value. Such a construct is evaluated
as an assignment.

+------------------------------+---------------------------------------------------------------------------------+
| Assignment                   | Explanation                                                                     |
+==============================+=================================================================================+
| | $x: value                  | | assigns ``value`` to the local variable ``$x``                                |
+------------------------------+---------------------------------------------------------------------------------+
| | $.x: value                 | | assign ``value`` to the object's property                                     |
| | $this.x: value             |                                                                                 |
+------------------------------+---------------------------------------------------------------------------------+
| | $.x: $.y                   | | copies the value of the property ``y`` to the property ``x``                  |
+------------------------------+---------------------------------------------------------------------------------+
| | $x: [$a, $b]               | | sets ``$x`` to the array of two values: ``$a`` and ``$b``                     |
+------------------------------+---------------------------------------------------------------------------------+
| | $x:                        | | structures of any level of complexity can be evaluated                        |
| |   SomeKey:                 |                                                                                 |
| |     NestedKey: $variable   |                                                                                 |
+------------------------------+---------------------------------------------------------------------------------+
| | $.x[0]: value              | | assigns ``value`` to the first array entry of the ``x`` property              |
+------------------------------+---------------------------------------------------------------------------------+
| | $.x: $.x.append(value)     | | appends ``value`` to the array in the ``x`` property                          |
+------------------------------+---------------------------------------------------------------------------------+
| | $.x: $.x.insert(1, value)  | | inserts ``value`` into position 1 of the array in the ``x`` property          |
+------------------------------+---------------------------------------------------------------------------------+
| | $x: list($a, $b).delete(0) | | sets ``$x`` to the list without the item at index 0                           |
+------------------------------+---------------------------------------------------------------------------------+
| | $.x.key.subKey: value      | | deep dictionary modification                                                  |
| | $.x[key][subKey]: value    |                                                                                 |
+------------------------------+---------------------------------------------------------------------------------+


Block constructs
++++++++++++++++

Block constructs control a program flow. They are dictionaries that have
strings as all their keys.

The following block constructs are available:

+---------------------------+---------------------------------------------------------------------------------------+
| Assignment                | Explanation                                                                           |
+===========================+=======================================================================================+
| | Return: value           | | Returns value from a method                                                         |
+---------------------------+---------------------------------------------------------------------------------------+
| | If: predicate()         | | ``predicate()`` is a YAQL expression that must be evaluated to ``True`` or ``False``|
| | Then:                   |                                                                                       |
| |   - code                | | The ``Else`` section is optional                                                    |
| |   - block               | | One-line code blocks can be written as scalars rather than an array.                |
| | Else:                   |                                                                                       |
| |   - code                |                                                                                       |
| |   - block               |                                                                                       |
+---------------------------+---------------------------------------------------------------------------------------+
| | While: predicate()      | | ``predicate()`` must be evaluated to ``True`` or ``False``                          |
| | Do:                     |                                                                                       |
| |   - code                |                                                                                       |
| |   - block               |                                                                                       |
+---------------------------+---------------------------------------------------------------------------------------+
| | For: variableName       | | ``collection`` must be a YAQL expression returning iterable collection or           |
| | In: collection          |    evaluatable array as in assignment instructions, for example, ``[1, 2, $x]``       |
| | Do:                     |                                                                                       |
| |   - code                | | Inside a code block loop, a variable is accessible as ``$variableName``             |
| |   - block               |                                                                                       |
+---------------------------+---------------------------------------------------------------------------------------+
| | Repeat:                 | | Repeats the code block specified number of times                                    |
| | Do:                     |                                                                                       |
| |   - code                |                                                                                       |
| |   - block               |                                                                                       |
+---------------------------+---------------------------------------------------------------------------------------+
| | Break:                  | | Breaks from loop                                                                    |
+---------------------------+---------------------------------------------------------------------------------------+
| | Match:                  | | Matches the result of ``$valExpression()`` against a set of possible values         |
| |   case1:                |   (cases). The code block of first matched case is executed.                          |
| |     - code              |                                                                                       |
| |     - block             | | If no case matched and the default key is present                                   |
| |   case2:                |   than the ``Default`` code block get executed.                                       |
| |     - code              | | The case values are constant values (not expressions).                              |
| |     - block             |                                                                                       |
| | Value: $valExpression() |                                                                                       |
| | Default:                |                                                                                       |
| |   - code                |                                                                                       |
| |   - block               |                                                                                       |
+---------------------------+---------------------------------------------------------------------------------------+
| | Switch:                 | | All code blocks that have their predicate evaluated to ``True`` are executed,       |
| |   $predicate1():        |   but the order of predicate evaluation is not fixed.                                 |
| |     - code              |                                                                                       |
| |     - block             |                                                                                       |
| |   $predicate2():        |                                                                                       |
| |     - code              |                                                                                       |
| |     - block             |                                                                                       |
| | Default:                | | The ``Default`` key is optional.                                                    |
| |   - code                |                                                                                       |
| |   - block               | | If no predicate evaluated to ``True``, the ``Default`` code block get executed.     |
+---------------------------+---------------------------------------------------------------------------------------+
| | Parallel:               | | Executes all instructions in code block in a separate green threads in parallel.    |
| |   - code                |                                                                                       |
| |   - block               |                                                                                       |
| | Limit: 5                | | The limit is optional and means the maximum number of concurrent green threads.     |
+---------------------------+---------------------------------------------------------------------------------------+
| | Try:                    | | Try and Catch are keywords that represent the handling of exceptions due to data    |
| |   - code                |   or coding errors during program execution. A ``Try`` block is the block of code in  |
| |   - block               |   which exceptions occur. A ``Catch`` block is the block of code, that is executed if |
| | Catch:                  |   an exception occurred.                                                              |
| | With: keyError          | | Exceptions are not declared in Murano PL. It means that exceptions of any types can |
| | As: e                   |   be handled and generated. Generating of exception can be done with construct:       |
| | Do:                     |   ``Throw: keyError``.                                                                |
| |   - code                |                                                                                       |
| |   - block               |                                                                                       |
| | Else:                   | | The ``Else`` is optional block. ``Else`` block is executed if no exception occurred.|
| |   - code                |                                                                                       |
| |   - block               |                                                                                       |
| | Finally:                | | The ``Finally`` also is optional. It's a place to put any code that will            |
| |   - code                |   be executed, whether the try-block raised an exception or not.                      |
| |   - block               |                                                                                       |
+---------------------------+---------------------------------------------------------------------------------------+

Notice, that if you have more than one block construct in your workflow, you
need to insert dashes before each construct. For example::

  Body:
    - If: predicate1()
      Then:
        - code
        - block
    - While: predicate2()
      Do:
        - code
        - block


.. _object-model:

Object model
------------

Object model is a JSON serialized representation of objects and their
properties. Everything you do in the OpenStack dashboard is reflected
in an object model. The object model is sent to the Application catalog engine
when the user decides to deploy the built environment. On the engine
side, MuranoPL objects are constructed and initialized from the received
Object model, and a predefined method is executed on the root object.

Objects are serialized to JSON using the following template:

.. code-block:: json
   :linenos:

   {
       "?": {
           "id": "globally unique object ID (UUID)",
           "type": "fully namespace-qualified class name",

           "optional designer-related entries can be placed here": {
               "key": "value"
           }
       },

       "classProperty1": "propertyValue",
       "classProperty2": 123,
       "classProperty3": ["value1", "value2"],

       "reference1": {
           "?": {
               "id": "object id",
               "type": "object type"
           },

           "property": "value"
       },

       "reference2": "referenced object id"
   }

Objects can be identified as dictionaries that contain the ``?`` entry.
All system fields are hidden in that entry.

There are two ways to specify references:

#. ``reference1`` as in the example above. This method allows inline
   definition of an object. When the instance of the referenced object
   is created, an outer object becomes its parent/owner that is responsible
   for the object. The object itself may require that its parent
   (direct or indirect) be of a specified type, like all applications
   require to have ``Environment`` somewhere in a parent chain.

#. Referring to an object by specifying other object ID. That object must
   be defined elsewhere in an object tree. Object references distinguished
   from strings having the same value by evaluating property contracts.
   The former case would have ``$.class(Name)`` while the later - the
   ``$.string()`` contract.
