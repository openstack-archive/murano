.. _reflection:

Reflection capabilities in MuranoPL.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reflection provides objects that describes MuranoPL classes and packages.

The first important function is ``typeinfo`` . Usage:

.. code-block:: yaml

    $typeInfo: typeinfo($someObject)



Now ``$typeInfo`` variable contains instance of type of ``$someObject`` (``MuranoClass`` instance).

MuranoPL provide following abilities to reflection:


.. _types_reflection:

Types
-----

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - Property
     - Description
   * - ``name``
     - name of MuranoPL class
   * - ``version``
     - version (`SemVer`_) of MuranoPL class.
   * - ``ancestors``
     - list of class ancestors
   * - ``properties``
     - list of class properties. See :ref:`properties_reflection`
   * - ``package``
     - package information. See :ref:`package_reflection`
   * - ``methods``
     - list of methods. See :ref:`methods_reflection`
   * - ``type``
     - reference to type, which can be used as argument in engine functions



*Example*

.. code-block:: yaml

   - $typeInfo: typeinfo($)
   ...
   # log name, version and package name of this class
   - $log.info("This is "{class_name}/{version} from {package}",
        class_name => $typeInfo.name,
        version => str($typeInfo.version),
        package => $typeInfo.package.name))
   - $log.info("Ancestors:")
   - For: ancestor
     In: $typeInfo.ancestors
     Do:
       #log all ancestors names
       - $log.info("{ancestor_name}", ancestor_name => $ancestor.name)
   # log full class version
   - $log.info("{version}", version => str($typeInfo.version))
   # create object with same class
   - $newObject = new($typeInfo.type)


.. _properties_reflection:

Properties
----------


Property introspection
++++++++++++++++++++++

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - Property
     - Description
   * - ``name``
     - name of property
   * - ``hasDefault``
     - boolean value. `True`, if property has default value, `False` otherwise
   * - ``usage``
     - `Usage` property's field. See :ref:`property_usage` for details
   * - ``declaringType``
     - type - owner of declared property


Property access
+++++++++++++++

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - Methods
     - Description
   * - ``$property.setValue($target, $value)``
     - set value of ``$property`` for object ``$target`` to ``$value``
   * - ``$property.getValue($target)``
     - get value of ``$property`` for object ``$target``

*Example*

.. code-block:: yaml

    - $typeInfo: typeinfo($)
    ...
    # select first property
    - $selectedPropety: $typeInfo.properties.first()
    # log property name
    - $log.info("Hi, my name is {p_name}, p_name => $selectedProperty.name)
    # set new property value
    - $selectedProperty.setValue($, "new_value")
    # log new property value using reflection
    - $log.info("My new value is {value}", value => $selectedProperty.getValue($))
    # also, if property static, $target can be null
    - $log.info("Static property value is {value},
        value => $staticProperty.getValue(null))



.. _package_reflection:

Packages
--------

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - Property
     - Description
   * - ``types``
     - list of types, declared in package
   * - ``name``
     - package name
   * - ``version``
     - package version


*Example*

.. code-block:: yaml

    - $typeInfo: typeinfo($)
    ...
    - $packageRef: $typeInfo.package
    - $log.info("This is package {p_name}/{p_version}",
        p_name => $packageRef.name,
        p_version => str($packageRef.version))
    - $log.info("Types in package:")
    - For: type_
      In: $packageRef.types
      Do:
        - $log.info("{typename}", typename => type_.name)


.. _methods_reflection:

Methods
-------

Methods properties
++++++++++++++++++

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - Property
     - Description
   * - ``name``
     - method's name
   * - ``declaringType``
     - type - owner of declared method
   * - ``arguments``
     - list of method's arguments. See :ref:`arguments_reflection`


Method invoking
+++++++++++++++

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - Methods
     - Description
   * - ``$method.invoke($target, $arg1, ... $argN, kwarg1 => value1, ..., kwargN => valueN)``
     - call ``$target``'s method $method with ``$arg1``, ..., ``$argN`` positional arguments and ``kwarg1``, .... ``kwargN`` named arguments

*Example*

.. code-block:: yaml

    - $typeInfo: typeinfo($)
    ...
    # select single method by name
    - $selectedMethod: $typeInfo.methods.where($.name = sampleMethodName).single()
    # log method name
    - $log.info("Method name: {m_name}", m_name => $selectedMethod.name)
    # log method arguments names
    - For: argument
      In: $selectedMethod.arguments
      Do:
         - $log.info("{name}", name => $argument.name)
    # call method with positional argument 'bar' and named `baz` == 'baz'
    - $selectedMethod.invoke($, 'bar', baz => baz)


.. _arguments_reflection:

Method arguments
----------------

.. list-table::
   :header-rows: 1
   :widths: 20 80
   :stub-columns: 0
   :class: borderless

   * - Property
     - Description
   * - ``name``
     - argument's name
   * - ``hasDefault``
     - `True` if argument has default value, `False` otherwise
   * - ``declaringMethod``
     - method - owner of argument
   * - ``usage``
     - argument's usage type.  See :ref:`method_arguments` for details

.. code-block:: yaml

    - $firstArgument: $selectedMethod.arguments.first()
    # store argument's name
    - $argName: $firstArgument.name
    # store owner's name
    - $methodName: $firstArgument.declaringMethod.name
    - $log.info("Hi, my name is {a_name} ! My owner is {m_name}",
        a_name => $argName,
        m_name => $methodName)


.. Links:
.. _`SemVer`: http://semver.org


