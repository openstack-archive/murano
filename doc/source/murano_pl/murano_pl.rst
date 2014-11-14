..
      Copyright 2014 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http//www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

YAML
====

YAML is human-readable data serialization format that is a superset of JSON. Unlike JSON YAML was designed to be read and written by humans and relies on visual indentation to denote nesting of data structures. This is similar to how Python uses indentation for block structures instead of curly brackets in most C-like languages. Also YAML can contain more data types comparing to JSON. See http://yaml.org/ for detailed description of YAML.

MuranoPL was designed to be representable in YAML so that MuranoPL code could remain readable and structured. Thus usually MuranoPL files are YAML encoded documents. But MuranoPL engine itself doesn't  deal directly with YAML documents and it is up to hosting application to locate and deserialize definitions of particular classes. This gives hosting application ability to control where those definitions can be found (file system, database, remote repository etc) and possibly use some other serialization formats instead of YAML.

MuranoPL engine relies on host deserialization code to automatically detect YAQL expressions in source definition and to provide them as instances of YaqlExpression class rather than plain strings. Usually YAQL expressions can be distinguished by presence of $ (dollar sign) and operators but in YAML developer can always explicitly state the type by using YAML tags. So
   ::

     Some text - a string,
     $.something() - YAQL
     "$.something()" - string (because of quote marks)
     !!str $ - a string (because of YAML tag)
     !yaql "text" - YAQL  (because of YAML tag)


YAQL
====

YAQL (Yet Another Query Language) is a query language that was also designed as part of Murano project. MuranoPL makes an extensive use of YAQL. YAQL description can be found here: https://github.com/ativelkov/yaql

In simple words YAQL is a language for expression evaluation. ``2 + 2, foo() > bar(), true != false`` are all valid YAQL expressions. The interesting thing in YAQL is that it has no built in list of functions. Everything YAQL can access is customizable. YAQL cannot call any function that was not explicitly registered to be accessible by YAQL. The same is true for operators. So the result of expression 2 * foo(3, 4) is completely depended on explicitly provided implementations of "foo" and "operator_*".
YAQL uses dollar sign ($) to access external variables (that are also explicitly provided by host application) and function arguments. ``$variable`` is a syntax to get the value of variable "$variable",
$1, $2 etc are the names for function arguments. "$" is a name for current object - data on which the expression is evaluated or a name of a single argument. Thus $ in the beginning of expression and $ in middle of it can refer to different things.

YAQL has a lot of functions out of the box that can be registered in YAQL context. For example

``$.where($.myObj.myScalar > 5 and $.myObj.myArray.len() > 0 and $.myObj.myArray.any($ = 4)).select($.myObj.myArray[0])`` can be executed on ``$ = array`` of objects and has a result of another array that is a filtration and projection of a source data. This is very similar to how SQL works but uses more Python-like syntax.

Note that there is no assignment operator in YAQL and '=' means comparision operator that is what '==' means in Python.

Because YAQL has no access to underlying operating system resources and 100% controllable by the host it is secure to execute YAQL expressions without establishing a trust to executed code. Also because of the functions are not predefined different functions may be accessible in different contexts. So the YAQL expressions that are used to specify property contracts are not necessarily valid in workflow definitions.

Common class structure
======================

Here is a common template for class declarations. In sections below I'm going to explain what each section means. Note that it is in YAML format.

.. code-block:: yaml

     Name: class name
     Namespaces: namespaces specification
     Extends: [list of parent classes]
     Properties: properties declaration
     Workflow:
         methodName:
             Arguments:
                 - list
                 - of
                 - arguments
             Body:
                 - list
                 - of
                 - instructions

Thus MuranoPL class is a YAML dictionary with predefined key names. All keys except for Name are optional and can be omitted (but must be valid if present)

Class name
----------

Class names are alphanumeric names of the classes. By tradition all class names begin with upper-case letter and written in PascalCasing.

In Murano all class names are globally unique. This achieved by means of namespaces. Class name may have explicit namespace specification (like ns:MyName) or implicit (just MyName which would be equal to =:MyName if = was a valid in name specification)

Namespaces
----------

Namespaces declaration specifies prefixes that can be used in class body to make long class names shorter.

.. code-block:: yaml

     Namespaces:
         =: io.murano.services.windows
         srv: io.murano.services
         std: io.murano

In example above class name srv:Something would be automatically translated to "io.murano.services.Something".

"=" means "current namespace" so that "MyClass" would mean "io.murano.services.windows.MyClass" in example above.

If class name contains period sign (.) in its name then it is assumed to be already fully namespace-qualified and is not expanded. Thus ns.Myclass would remain as is.

To make class names globally unique it is recommended to have developer's domain name as part of namespace (as in example, similar to Java)

Extends
-------

MuranoPL supports multiple inheritance. If present, Extends section lists base classes that are extended. If the list consists of single entry then it may be written as a scalar string instead of array. If no parents specified (or a key is omitted) then "io.murano.Object" is assumed making it the root class for all class hierarchies.

Properties
----------

Properties are class attributes that together with methods form public class interface. Usually (but not always) properties are the values and references to other objects that are required to be entered in environment designer prior to workflow invocation.

Properties have the following declaration format:

.. code-block:: yaml

     propertyName:
         Contract: property contract
         Usage: property usage
         Default: property default

Contract
^^^^^^^^

Contracts are YAQL expressions that say what type of value is expected for the property as well as additional constraints imposed on the property. 

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
| $.class(ns:Name).check($.p = 12)                          |  value must be of type ns:Name and have a property 'p' equal to 12                              |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int()]                                               |  array of integers. Similar for other types                                                     |
| | [$.int().notNull()]                                     |                                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| [$.int().check($ > 0)]                                    |  array of positive integers (thus not null)                                                     |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| [$.int(), $.string()]                                     |  array that has at least two elements, first is int and others are strings                      |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | [$.int(), 2]                                            |  | array of ints with at least 2 items                                                          |
| | [$.int(), 2, 5]                                         |  | ... and maximum of 5 items                                                                   |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| { A: $.int(), B: [$.string()] }                           |  dictionary with 'A' key of type int and 'B' - array of strings                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | $                                                       |  any scalar or data structure as is                                                             |
| | []                                                      |  any array                                                                                      |
| | {}                                                      |  any dictionary                                                                                 |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| { $.string().notNull(): $.int().notNull() }               |  dictionary string -> int                                                                       |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+
| | A: StringMap                                            | dictionary with 'A' key that must be equal to 'StringMap' and other keys be any scalar or data  |
| | $.string().notNull(): $                                 | structure                                                                                       |
+-----------------------------------------------------------+-------------------------------------------------------------------------------------------------+

Usage
^^^^^

Usage states purpose of the property. This implies who and how can access it. The following usages are available:

===========  ==================================================================================================================================================
Property     Explanation
===========  ==================================================================================================================================================
``In``       Input property. Values of such properties are obtained from user and cannot be modified in MuranoPL workflows. This is default value for Usage key
``Out``      The value is obtained from executing MuranoPL workflow and cannot be modified by the user
``InOut``    Value can be edited by both user and workflow
``Const``    The same as In but once workflow is executed the property cannot be changed neither by user not the workflow
``Runtime``  Property is visible only from within workflows. It neither read from input neither serialized to workflow output
===========  ==================================================================================================================================================

Usage attribute is optional and can be omitted (which implies In).

If the workflow tries to write to a property that is not declared with one of the types above it is considered to be private and accessible only to that class (and not serialized to output and thus would be lost upon next deployment). Attempt to read property that wasn't initialized causes exception to be thrown.

Default
^^^^^^^

Default is a value that would be used if the property value wasn't mentioned in input object model (but not when it is provided as null). Default (if specified) must conform to declared property contract. If Default is not specified then null is the default.

For properties that are references to other classes Default can modify default values for referenced value. For example
   ::

     p:
       Contract: $.class(MyClass)
       Default: {a: 12}

would override default for 'a' property of MyClass for instance of MyClass that is created for this property.

Workflow
--------

Workflows are the methods that together describe how the entities that are represented by MuranoPL classes are deployed.

In typical scenario root object in input data model is of type io.murano.Environment and has a "deploy" method. Invoking this method causes a series of infrastructure activities (typically by modifying Heat stack) and VM agents commands that cause execution of deployment scripts. Workflow role is to map data from input object model (or result of previously executed actions) to parameters of those activities and to initiate those activities in correct order.
Methods have input parameters and can return value to the caller.
Methods defined in Workflow section of the class using the following template:

   ::

    methodName:
        Arguments:
            - list
            - of
            - arguments
        Body:
            - list
            - of
            - instructions

Arguments are optional and (if specified) declared using the same syntax as class properties except for Usage attribute that is meaningless for method parameters. E.g. arguments also have a contract and optional default.

Method body is an array of instructions that got executed sequentially. There are 3 types of instructions that can be found in workflow body: expressions, assignment and block constructs.

Expressions
^^^^^^^^^^^

Expressions are YAQL expressions that are executed for their side effect. All accessible object methods can be called in expression using $obj.methodName(arguments) syntax.

+-------------------------------------------+----------------------------------------------------------------+
|  Expression                               |  Explanation                                                   |
+===========================================+================================================================+
| | ``$.methodName()``                      |  invoke method 'methodName' on this (self) object              |
| | ``$this.methodName()``                  |                                                                |
+-------------------------------------------+----------------------------------------------------------------+
| | ``$.property.methodName()``             |  invocation of method on object that is in 'property' property |
| | ``$this.property.methodName()``         |                                                                |
+-------------------------------------------+----------------------------------------------------------------+
| ``$.method(1, 2, 3)``                     |  methods can have arguments                                    |
+-------------------------------------------+----------------------------------------------------------------+
| ``$.method(1, 2, thirdParameter => 3)``   |  named parameters also supported                               |
+-------------------------------------------+----------------------------------------------------------------+
| ``list($.foo().bar($this.property), $p)`` |  complex expressions can be constructed                        |
+-------------------------------------------+----------------------------------------------------------------+


Assignment
^^^^^^^^^^

Assignments are single-key dictionaries with YAQL expression as key and arbitrary structure as a value. Such construct evaluated as assignment.

+--------------------------------+-------------------------------------------------------------------------------------------------+
| Assignment                     | Explanation                                                                                     |
+================================+=================================================================================================+
| ``$x: value``                  | assigns ‘value’ to local variable $x                                                            |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x: value``                 | assign value to object’s property                                                               |
| ``$this.x: value``             |                                                                                                 |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x: $.y``                   | copy value of property 'y' to property 'x'                                                      |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$x: [$a, $b]``               | sets $x to array of 2 values $a and $b                                                          |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| | ``$x:``                      | structures of any level of complexity can be evaluated                                          |
| |   ``SomeKey:``               |                                                                                                 |
| |     ``NestedKey: $variable`` |                                                                                                 |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x[0]: value```             | assign value to a first array entry of property x                                               |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| ``$.x.append(): value``        | append value to array in property x                                                             |
+--------------------------------+------------------------------+------------------------------------------------------------------+
| ``$.x.insert(1): value``       | insert value into position 1                                                                    |
+--------------------------------+-------------------------------------------------------------------------------------------------+
| | ``$.x.key.subKey: value``    | deep dictionary modification                                                                    |
| | ``$.x[key][subKey]: value``  |                                                                                                 |
+--------------------------------+-------------------------------------------------------------------------------------------------+


Block constructs
^^^^^^^^^^^^^^^^

Block constructs control program flow. Block constructs are dictionaries that have strings as all its keys.
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
| | ``Else:``                     | one-line code blocks can be written as a scalars rather than array.                    |
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
| | ``Repeat:``                   | repeat code block specified number of times                                            |
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
| |     ``- code``                | case values are constant values (not expressions)                                      |
| |     ``- block``               |                                                                                        |
| | ``Value: $valueExpression()`` |                                                                                        |
| | ``Default:``                  |                                                                                        |
| |     ``- code``                |                                                                                        |
| |     ``- block``               |                                                                                        |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``Switch:``                   | all code blocks that have their predicate evaluated to true are executed but the order |
| |   ``$predicate1() :``         |    of predicate evaluation is not fixed                                                |
| |       ``- code``              |                                                                                        |
| |       ``- block``             |                                                                                        |
| |   ``$predicate2() :``         |                                                                                        |
| |       ``- code``              |                                                                                        |
| |       ``- block``             |                                                                                        |
| | ``Default:``                  | default key is optional.                                                               |
| |     ``- code``                |                                                                                        |
| |     ``- block``               | if no predicate evaluated to true than Default code block get executed.                |
+---------------------------------+----------------------------------------------------------------------------------------+
| | ``Parallel:``                 | executes all instructions in code block in separate green threads in parallel          |
| |     ``- code``                |                                                                                        |
| |     ``- block``               |                                                                                        |
| | ``Limit: 5``                  | limit is optional and means the maximum number of concurrent green threads.            |
+---------------------------------+----------------------------------------------------------------------------------------+

Object model
------------

Object model is JSON-serialized representation of objects and their properties. Everything user does in environment builder (dashboard) is reflected in object model. Object model is sent to App Catalog engine upon user decides to deploy built environment. On engine side MuranoPL objects are constructed and initialized from received Object model and predefined method is executed on a root object.


Objects serialized to JSON using the following template:

.. code-block:: yaml

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

There are 2 ways to specify references. The first method ("reference1" in example above) allow inline definition of object. When instance of referenced object is created outer object becomes its parent (owner) that is responsible for the object. The object itself may require that its parent (direct or indirect) be of specified type (like all application require to have Environment somewhere in parent chain).

Second way to reference object is by specifying other object id. That object must be defined somewhere else in object tree. Object references distinguished from strings having the same value by evaluating property contracts. The former case would have $.class(Name) while the later $.string() contract.
