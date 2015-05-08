.. _class_templ:

Common class structure
~~~~~~~~~~~~~~~~~~~~~~

Here is a common template for class declarations. Note, that it is in YAML format.

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

Thus MuranoPL class is a YAML dictionary with predefined key names. All keys except for Name are optional and can be omitted (but must be valid if present).

Class name
----------

Class names are alphanumeric names of the classes. By tradition all class names begin with upper-case letter and written in PascalCasing.

In Murano all class names are globally unique. This achieved by means of namespaces. Class name may have explicit namespace specification (like ns:MyName) or implicit (just MyName which would be equal to =:MyName if = was valid in a name specification).

Namespaces
----------

Namespaces declaration specifies prefixes that can be used in class body to make long class names shorter.

.. code-block:: yaml

     Namespaces:
         =: io.murano.services.windows
         srv: io.murano.services
         std: io.murano

In example above class name srv:Something would be automatically translated to "io.murano.services.Something".

"=" means "current namespace", so that "MyClass" would mean "io.murano.services.windows.MyClass" in the example above.

If class name contains period sign (.) in its name then it is assumed to be already fully namespace-qualified and is not expanded. Thus ns.Myclass would remain as is.

To make class names globally unique it is recommended to have a developer's domain name as a part of the namespace (as in the example, similar to Java).

Extends
-------

MuranoPL supports multiple inheritance. If present, Extends section shows base classes that are extended. If the list consists of a single entry, then it may be written as a scalar string instead of an array. If no parents specified (or a key is omitted) then "io.murano.Object" is assumed making it the root class for all class hierarchies.

Properties
----------

Properties are class attributes that together with methods create public class interface. Usually (but not always) properties are the values and references to other objects that are required to be entered in a designer environment prior to a workflow invocation.

Properties have the following declaration format:

.. code-block:: yaml

     propertyName:
         Contract: property contract
         Usage: property usage
         Default: property default

Contract
^^^^^^^^

Contracts are YAQL expressions that say what type of value is expected for the property as well as additional constraints imposed on a property.

+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
|  Operation                                                |  Definition                                                                                     |
+===========================================================+=================================================================================================+
| $.int()                                                   |  integer value (may be null). String values that consist of digits would be converted to integer|
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| $.int().notNull()                                         |  mandatory integer                                                                              |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.string()                                              |  the same for strings. If the supplied value is not a string it will be converted to string     |
| | $.string().notNull()                                    |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.bool()                                                |  bools are true and false. 0 is converted to false, other integers to true                      |
| | $.bool().notNull()                                      |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $.class(ns:ClassName)                                   |  value must be a reference to an instance of specified class name                               |
| | $.class(ns:ClassName).notNull()                         |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| $.class(ns:ClassName, ns:DefaultClassName)                |  create instance of ns:DefaultClassName class if no instance provided                           |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| $.class(ns:Name).check($.p = 12)                          |  the value must be of type ns:Name and have a property 'p' equal to 12                          |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int()]                                               |  the array of integers. Similar for other types                                                 |
| | [$.int().notNull()]                                     |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| [$.int().check($ > 0)]                                    |  the array of positive integers (thus not null)                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| [$.int(), $.string()]                                     |  the array that has at least two elements, first is int and others are strings                  |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int(), 2]                                            |  | the array of ints with at least 2 items                                                      |
| | [$.int(), 2, 5]                                         |  | ... and maximum of 5 items                                                                   |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| { A: $.int(), B: [$.string()] }                           |  the dictionary with 'A' key of type int and 'B' - the array of strings                         |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $                                                       |  any scalar or data structure as is                                                             |
| | []                                                      |  any array                                                                                      |
| | {}                                                      |  any dictionary                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| { $.string().notNull(): $.int().notNull() }               |  dictionary string -> int                                                                       |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | A: StringMap                                            | the dictionary with 'A' key that must be equal to 'StringMap' and other keys be any scalar or   |
| | $.string().notNull(): $                                 | data structure                                                                                  |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+

Usage
^^^^^

Usage states purpose of the property. This implies who and how can access it. The following usages are available:

===========  =======================================================================================================================================================
Property     Explanation
===========  =======================================================================================================================================================
``In``       Input property. Values of such properties are obtained from a user and cannot be modified in MuranoPL workflows. This is a default value for Usage key.
``Out``      A value is obtained from executing MuranoPL workflow and cannot be modified by a user.
``InOut``    A value can be edited by both a user and a workflow.
``Const``    The same as In but once workflow is executed a property cannot be changed neither by a user nor by a workflow.
``Runtime``  A property is visible only from within workflows. It is neither read from input nor serialized to a workflow output.
===========  =======================================================================================================================================================

Usage attribute is optional and can be omitted (which implies In).

If the workflow tries to write to a property that is not declared with one of the types above it is considered to be private and accessible only to that class (and not serialized to output and thus would be lost upon the next deployment). An attempt to read property that was not initialized causes an exception to be thrown.

Default
^^^^^^^

Default is a value that would be used if the property value was not mentioned in input object model (but not when it is provided as null). Default (if specified) must conform to a declared property contract. If Default is not specified then null is the default.

For properties that are references to other classes Default can modify default values for the referenced value. For example:
   ::

     p:
       Contract: $.class(MyClass)
       Default: {a: 12}

would override default for 'a' property of MyClass for instance of MyClass that is created for this property.

Workflow
--------

Workflows are the methods that together describe how the entities that are represented by MuranoPL classes are deployed.

In typical scenario the root object in an input data model is of type io.murano.Environment and has a "deploy" method. Invoking this method causes a series of infrastructure activities (typically by modifying Heat stack) and VM agents commands that cause execution of deployment scripts. A role of the workflow is to map data from the input object model (or a result of previously executed actions) to parameters of those activities and to initiate those activities in correct order.

workflow -> Methods:

Methods have input parameters and can return a value to a caller.
Methods defined in Workflow section of the class using the following template:

   ::

    methodName:
        Usage: Action
        Arguments:
            - list
            - of
            - arguments
        Body:
            - list
            - of
            - instructions

Action is optional parameter that specify methods to be executed by direct triggering after deployment.

Arguments are optional and (if specified) declared using the same syntax as class properties except for Usage attribute that is meaningless for method parameters. For example, arguments also have a contract and optional default.

Method body is an array of instructions that got executed sequentially. There are 3 types of instructions that can be found in a workflow body: expressions, assignments and block constructs.

Expressions
^^^^^^^^^^^

Expressions are YAQL expressions that are executed for their side effect. All accessible object methods can be called in the expression using $obj.methodName(arguments) syntax.

+-------------------------------------------+----------------------------------------------------------------+
|  Expression                               |  Explanation                                                   |
+===========================================+================================================================+
| | ``$.methodName()``                      |  invoke method 'methodName' on this (self) object              |
| | ``$this.methodName()``                  |                                                                |
+-------------------------------------------+----------------------------------------------------------------+
| | ``$.property.methodName()``             |  invocation of method on object that is in 'property' property |
| | ``$this.property.methodName()``         |                                                                |
+-------------------------------------------+----------------------------------------------------------------+
| ``$.method(1, 2, 3)``                     |  methods may have arguments                                    |
+-------------------------------------------+----------------------------------------------------------------+
| ``$.method(1, 2, thirdParameter => 3)``   |  named parameters are also supported                           |
+-------------------------------------------+----------------------------------------------------------------+
| ``list($.foo().bar($this.property), $p)`` |  complex expressions can be constructed                        |
+-------------------------------------------+----------------------------------------------------------------+


Assignment
^^^^^^^^^^

Assignments are single-key dictionaries with YAQL expression as key and arbitrary structure as a value. Such a construct is evaluated as an assignment.

+--------------------------------+-------------------------------------------------------------------------------------------------+
| Assignment                     | Explanation                                                                                     |
+================================+=================================================================================================+
| ``$x: value``                  | assigns ‘value’ to the local variable $x                                                        |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x: value``                 | assign the value to the object’s property                                                       |
| ``$this.x: value``             |                                                                                                 |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x: $.y``                   | copy the value of the property 'y' to the property 'x'                                          |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$x: [$a, $b]``               | sets $x to the array of 2 values $a and $b                                                      |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| | ``$x:``                      | structures of any level of complexity can be evaluated                                          |
| |   ``SomeKey:``               |                                                                                                 |
| |     ``NestedKey: $variable`` |                                                                                                 |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x[0]: value```             | assign the value to a first array entry of the property x                                       |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x.append(): value``        | append the value to array in the property x                                                     |
+--------------------------------+------------------------------+------------------------------------------------------------------+
| ``$.x.insert(1): value``       | insert the value into the position 1                                                            |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| | ``$.x.key.subKey: value``    | deep dictionary modification                                                                    |
| | ``$.x[key][subKey]: value``  |                                                                                                 |
+--------------------------------+-------------------------------------------------------------------------------------------------+


Block constructs
^^^^^^^^^^^^^^^^

Block constructs control a program flow. Block constructs are dictionaries that have strings as all its keys.
The following block constructs are available:

+---------------------------------+----------------------------------------------------------------------------------------+
| Assignment                      | Explanation                                                                            |
+=================================+========================================================================================+
| ``Return: value``               | return value from a method                                                             |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``If: predicate()``           | predicate() is YAQL expressions that must be evaluated to true or false.               |
| | ``Then:``                     |                                                                                        |
| |   ``- code``                  | else part is optional                                                                  |
| |   ``- block``                 |                                                                                        |
| | ``Else:``                     | one-line code blocks can be written as a scalars rather than an array.                 |
| |   ``- code``                  |                                                                                        |
| |   ``- block``                 |                                                                                        |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``While: predicate()``        | predicate() must be evaluated to true or false                                         |
| | ``Do:``                       |                                                                                        |
|   | ``- code``                  |                                                                                        |
|   | ``- block``                 |                                                                                        |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``For: variableName``         | collection must be YAQL expression returning iterable collection or                    |
| | ``In: collection``            |     evaluatable array as in assignment instructions (like [1, 2, $x])                  |
| | ``Do:``                       |                                                                                        |
| |   ``- code``                  | inside code block loop variable is accessible as $variableName                         |
| |   ``- block``                 |                                                                                        |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``Repeat:``                   | repeat the code block specified number of times                                        |
| | ``Do:``                       |                                                                                        |
| |   ``- code``                  |                                                                                        |
| |   ``- block``                 |                                                                                        |
+---------------------------------+----------------------------------------------------------------------------------------+
| Break:                          | breaks from loop                                                                       |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``Match:``                    | matches result of $valueExpression() against set of possible values (cases).           |
| |  ``case1:``                   | the code block of first matched cased is executed.                                     |
| |     ``- code``                |                                                                                        |
| |     ``- block``               | if not case matched and Default key is present (it is optional)                        |
| |  ``case2:``                   |    than Default code block get executed.                                               |
| |     ``- code``                | case values are constant values (not expressions).                                     |
| |     ``- block``               |                                                                                        |
| | ``Value: $valueExpression()`` |                                                                                        |
| | ``Default:``                  |                                                                                        |
| |     ``- code``                |                                                                                        |
| |     ``- block``               |                                                                                        |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``Switch:``                   | all code blocks that have their predicate evaluated to true are executed, but the order|
| |   ``$predicate1() :``         |    of predicate evaluation is not fixed                                                |
| |       ``- code``              |                                                                                        |
| |       ``- block``             |                                                                                        |
| |   ``$predicate2() :``         |                                                                                        |
| |       ``- code``              |                                                                                        |
| |       ``- block``             |                                                                                        |
| | ``Default:``                  | the default key is optional.                                                           |
| |     ``- code``                |                                                                                        |
| |     ``- block``               | if no predicate evaluated to true than Default code block get executed.                |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``Parallel:``                 | executes all instructions in code block in separate green threads in parallel          |
| |     ``- code``                |                                                                                        |
| |     ``- block``               |                                                                                        |
| | ``Limit: 5``                  | the limit is optional and means the maximum number of concurrent green threads.        |
+---------------------------------+----------------------------------------------------------------------------------------+

Object model
------------

Object model is a JSON-serialized representation of objects and their properties. Everything user does in a builder environment (dashboard) is reflected in an object model. The object model is sent to App Catalog engine upon a user decides to deploy the built environment. On engine side MuranoPL objects are constructed and initialized from the received Object model and a predefined method is executed on the root object.


Objects are serialized to JSON using the following template:

.. code-block:: yaml
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

Objects can be identified as dictionaries that contain "?" entry. All system fields are hidden in that entry.

There are 2 ways to specify references. The first method ("reference1" in the example above) allows inline definition of an object. When instance of the referenced object is created, an outer object becomes its parent (owner) that is responsible for the object. The object itself may require that its parent (direct or indirect) be of a specified type (like all application require to have Environment somewhere in a parent chain).

The second way to reference an object is by specifying other object id. That object must be defined somewhere else in an object tree. Object references distinguished from strings having the same value by evaluating property contracts. The former case would have $.class(Name) while the later $.string() contract.
