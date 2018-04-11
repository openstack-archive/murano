.. _DynamicUISpec:

Dynamic UI definition specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The main purpose of Dynamic UI is to generate application creation
forms "on-the-fly".  The Murano dashboard does not know anything about
applications that will be presented in the catalog and which web forms are
required to create an application instance.  So all application definitions
should contain an instruction, which tells the dashboard how to create an
application and what validations need to be applied. This document will help
you to compose a valid UI definition for your application.

The UI definition should be a valid YAML file and may contain the following
sections (for version 2.x):

* **Version**
    Points out the syntax version in use. *Optional*
* **Templates**
    An auxiliary section, used together with an Application section
    to help with object model composing. *Optional*
* **Parameters**
    An auxiliary section for evaluated once parameters. *Optional*
* **ParametersSource**
    A static action name (ClassName.methodName) to call for additional
    parameters. *Optional*
* **Application**
    Object model description passed to murano engine and used for application
    deployment. *Required*
* **Forms**
    Web form definitions. *Required*

.. _DynamicUIversion:

Version
-------

The syntax and format of dynamic UI definitions may change over time, so the
concept of *format versions* is introduced. Each UI definition file may contain
a top-level section called *Version* to indicate the minimum version of Murano
Dynamic UI platform which is capable to process it.
If the section is missing, the format version is assumed to be latest supported.

The version consists of two non-negative integer segments, separated by a dot,
i.e. has a form of *MAJOR.MINOR*.
Dynamic UI platforms having the same MAJOR version component are compatible:
i.e. the platform having the higher version may process UI definitions with
lower versions if their MAJOR segments are the same.
For example, Murano Dynamic UI platform of version 2.2 is able to process UI
definitions of versions 2.0, 2.1 and 2.2, but is unable to process 3.0 or
1.9.

Currently, the latest version of Dynamic UI platform is 2.3. It is incompatible
with UI definitions of Version 1.0, which were used in Murano releases before
Juno.

.. note::

    Although the ``Version`` field is considered to be optional, its default
    value is the latest supported version. So if you intent to use applications
    with the previous stable murano version, verify that the version
    is set correctly.

Version history
~~~~~~~~~~~~~~~

+---------+-------------------------------------------------------------------+-------------------+
| Version | Changes                                                           | OpenStack Version |
+=========+===================================================================+===================+
| 1.0     | - Initial Dynamic UI implementation                               | Icehouse          |
+---------+-------------------------------------------------------------------+-------------------+
| 2.0     | - *instance* field support is dropped                             | Juno, Kilo        |
|         | - New *Application* section that describes engine object model    |                   |
|         | - New *Templates* section for keeping reusable pieces of Object   |                   |
+---------+-------------------------------------------------------------------+-------------------+
| 2.1     | - New *network* field provides a selection of networks and        | Liberty           |
|         |   their subnetworks as a dropdown populated with those which are  |                   |
|         |   available to the current tenant.                                |                   |
+---------+-------------------------------------------------------------------+-------------------+
| 2.2     | - Now *application name* is added automatically to the last       | Liberty           |
|         |   service form. It is needed for a user to recognize one          |                   |
|         |   created application from another in the UI. Previously all      |                   |
|         |   application definitions contained the *name* property. So to    |                   |
|         |   support backward compatibility, you need to manually remove     |                   |
|         |   *name* field from class properties.                             |                   |
+---------+-------------------------------------------------------------------+-------------------+
| 2.3     | - Now *password* field supports ``confirmInput`` flag and         | Mitaka            |
|         |   validator overloading with single ``regexpValidator`` or        |                   |
|         |   multiple *validators* attribute.                                |                   |
+---------+-------------------------------------------------------------------+-------------------+
| 2.4     | - Parameters and ParametersSource sections were added             | Ocata             |
|         | - ref() YAQL function were added to Application DSL               |                   |
|         | - YAQL expressions can be used anywhere in the form definition    |                   |
|         | - choice control accepts choices in dictionary format             |                   |
+---------+-------------------------------------------------------------------+-------------------+

Application
-----------

The Application section describes an *application object model*.
The model is a dictionary (document) of application property values (inputs).
Property value might be of any JSON-serializable type (including lists and
maps). In addition the value can be of an object type (another application,
application component, list of components etc.). Object properties are
represented either by the object model of the component (i.e. dictionary) or
by an object ID (string) if the object was already defined elsewhere.
Each object definition (including the one in Application itself) must have a
special ``?`` key called ``object header``. This key holds object metadata most
important of which is the object type name. Thus the Application might look
like this:

.. code-block:: yaml

   Application:
     ?:
        type: "com.myCompany.myNamespace.MyClass"
     property1: "string property value"
     property2: 123
     property3:
         key1: value1
         key2: [1, false, null]
     property4:
       ?:
          type: "com.myCompany.myNamespace.MyComponent"
       property: value

However in most cases the values in object model should come from input fields
rather than being static as in example above. To achieve this, object model
values can also be of a `YAQL <https://git.openstack.org/cgit/openstack/yaql/tree/README.rst>`
expression type. With expressions language it becomes possible to retrieve
input control values, do some calculations and data transformations (queries).
Any YAML value that is not enclosed in quote marks and conforms to the YAQL
syntax is considered to be a YAQL expression. There is also an explicit
YAML tag for the YAQL expressions: ``!yaql``.

So with the YAQL addition ``Application`` section might look like this:

.. code-block:: yaml

   Application:
     ?:
        type: "com.myCompany.myNamespace.MyClass"
     property1: $.formName.controlName
     property2: 100 + 20 + 3
     property3:
         !yaql "'KEY1'.toLower()'": !yaql "value1 + '1'"
         key2: [$parameter, not true]
     property4: null

When evaluating YAQL expressions ``$`` is set to the forms data (list of
dictionaries with cleaned validated forms' data) and templates and parameters
are available using $templateName ($parameterName) syntax. See below on
templates and parameters.

YAQL comes with hundreds of functions bundled. In addition to that there are
another four functions provided by murano dashboard:

* **generateHostname(pattern, index)** is used for a machine hostname template
  generation. It accepts two arguments: name pattern (string) and index
  (integer). If '#' symbol is present in name pattern, it will be replaced
  with the index provided. If pattern is an empty string, a random name will be
  generated.
* **repeat(template, times)** is used to produce a list of data snippets, given
  the template snippet (first argument) and number of times it should be
  reproduced (second argument). Inside that template snippet current step can
  be referenced as *$index*.
* **name()** returns current application name.
* **ref(templateName [, parameterName] [, idOnly])** is used to generate object
  definition from the template and then reference it several times in the
  object model. This function evaluates template ``templateName`` and
  fixes the result in parameters under ``parameterName`` key (or
  ``templateName`` if the second parameter was omitted). Then it generates
  object ID and places it into ``?/id`` field. On the first use of
  ``parameterName`` or if ``idOnly`` is ``false`` the function will return
  the whole object structure. On subsequent calls or if ``idOnly`` is
  ``true`` it will return the ID that was generated upon the first call.

Templates
---------

It is often that application object model contains number of similar instances
of the same component/class. For example it might be list of servers for
multi-server application or list of nodes or list of components. For such cases
UI definition markup allow to give the repeated object model snippet a name
and then refer to it by the name in the application object model.
Such snippets are placed into ``Templates`` section:

.. code-block:: yaml

   Templates:
     primaryController:
        ?:
          type: "io.murano.windows.activeDirectory.PrimaryController"
        host:
          ?:
            type: "io.murano.windows.Host"
          adminPassword: $.appConfiguration.adminPassword
          name: generateHostname($.appConfiguration.unitNamingPattern, 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage

      secondaryController:
        ?:
          type: "io.murano.windows.activeDirectory.SecondaryController"
        host:
          ?:
            type: "io.murano.windows.Host"
          adminPassword: $.appConfiguration.adminPassword
          name: generateHostname($.appConfiguration.unitNamingPattern, $index + 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage

Then the template can be inserted into application object model or to another
template using ``$templateName`` syntax. It is often case that it is used
together with ``repeat`` function to put several instances of template. In
this case templates may use of ``$index`` variable which will hold current
iteration number:

.. code-block:: yaml

   Application:
     ?:
       type: io.murano.windows.activeDirectory.ActiveDirectory
     primaryController: $primaryController
     secondaryControllers: repeat($secondaryController, $.appConfiguration.dcInstances - 1)


It is important to remember that templates are evaluated upon each access or
``repeat()`` iteration. Thus if the template has some properties set to a
random or generated values they are going to be different for each instance
of the template.

Another use case for templates is when single object is referenced several
times within application object model:

.. code-block:: yaml

   Templates:
     instance:
        ?:
          type: "io.murano.resources.LinuxMuranoInstance"
        image: myImage
        flavor: "m1.small"

   Application:
     ?:
       type: "com.example.MyApp"
     components:
       - ?:
           type: "com.example.MyComponentType1"
         instance: ref(instance)
       - ?:
           type: "com.example.MyComponentType2"
         instance: ref(instance)

In example above there are two components that uses the same server instance.
If this example had ``$instance`` instead of ``ref(instance)`` that would
be two unrelated servers based on the same template i.e. with the same image
and flavor, but not the same VM.


Parameters and ParametersSource
-------------------------------

Parameters are values that are used to parametrize the UI form and/or
application object model. Parameters are put into ``Parameters`` section and
accessed using ``$parameterName`` syntax:

.. code-block:: yaml

   Parameters:
     param1: "Hello!"

   Application:
     ?:
       type: "com.example.MyApp"
     stringProperty: $param1

Parameters are very similar to Templates with two differences:

#. Parameter values are evaluated only once per application instance at the
   very beginning whereas templates are evaluated on each access.

#. Parameter values can be used to initialize UI control attributes (e.g.
   initial text box value, list of choices for a drop down etc.)

However the most powerful feature about parameters is that their values
might be obtained from the application class. Here is how to do it:

#. In one of the classes in the MuranoPL package (usually the main application
   class define a static action method without arguments that returns a
   dictionary of variables:

    .. code-block:: yaml

       Name: "com.example.MyApp"
       Methods:
         myMethod:
           Usage: Static
           Scope: Public
           Body:
             # arbitrary MuranoPL code can be used here
             Return:
               var1: value1
               var2: 123

#. In UI definition file add
    .. code-block:: yaml

       ParametersSource: "com.example.MyApp.myMethod"

   The class name may be omitted. In this case the dashboard will try to use
   the type of Application object or package FQN for that purpose.

The values returned by the method are going to be merged into Parameters
section like if they were defined statically.





Forms
-----

This section describes markup elements for defining forms, which are currently
rendered and validated with Django. Each form has a name, field definitions
(mandatory), and validator definitions (optionally).

Note that each form is split into 2 parts:

* **input area** - left side, where all the controls are located
* **description area** - right side, where descriptions of the controls are located

Each field should contain:

* **name** -  system field name, could be any
* **type** - system field type

Currently supported options for **type** attribute are:

* *string* - text field (no inherent validations) with one-line text input
* *boolean* - boolean field, rendered as a checkbox
* *text* - same as string, but with a multi-line input
* *integer* - integer field with an appropriate validation, one-line text input
* *choice* - drop-down list of variants. Each variant has a display string that
  is going to be displayed to the user and associated key that is going to be
  a control value
* *password* - text field with validation for strong password, rendered as two
  masked text inputs (second one is for password confirmation)
* *clusterip* - specific text field, used for entering cluster IP address
  (validation for valid IP address syntax)
* *databaselist* - specific field, a list of databases (comma-separated list of
  databases' names, where each name has the following syntax first symbol
  should be latin letter or underscore; subsequent symbols can be latin
  letter, numeric, underscore, at the sign, number sign or dollar sign),
  rendered as one-line text input
* *image* - specific field, used for filtering suitable images by image type
  provided in murano metadata in glance properties.
* *flavor* - specific field, used for selection instance flavor from a list
* *keypair* - specific field, used for selecting a keypair from a list
* *azone* - specific field, used for selecting instance availability zone from
  a list
* *network* - specific field, used to select a network and subnet from a list
  of the ones available to the current user
* *securitygroup* - specific field, used for selecting a custom security group
  to assign to the instance
* *volume* - specific field, used for selecting a volume or a volume snapshot
  from a list of available volumes (and volume snapshots)
* any other value is considered to be a fully qualified name for some
  Application package and is rendered as a pair of controls: one for selecting
  already existing Applications of that type in an Environment, second - for
  creating a new Application of that type and selecting it

Other arguments (and whether they are required or not) depends on a
field's type and other attributes values. Most of them are standard Django
field attributes. The most common attributes are the following:

* **label** - name, that will be displayed in the form; defaults to **name**
  being capitalized.
* **description** - description, that will be displayed in the description area.
  Use YAML line folding character ``>-`` to keep the correct formatting during
  data transferring.
* **descriptionTitle** - title of the description, defaults to **label**;
  displayed in the description area
* **hidden** whether field should be visible or not in the input area.
  Note that hidden field's description will still be visible in the
  descriptions area (if given). Hidden fields are used storing some data to be
  used by other, visible fields.
* **minLength**, **maxLength** (for string fields) and **minValue**,
  **maxValue** (for integer fields) are transparently translated into django
  validation properties.
* **choices** - a choices for the ``choice`` control type. The format is
  ``[["key1", "display value1"], ["key2", "display value2"]]``. Starting from
  version 2.4 this can also be passed as a
  ``{key1: "display value1", key2: "display value2"}``
* **regexpValidator** - regular expression to validate user input. Used with
  *string* or *password* field.
* **errorMessages** - dictionary with optional 'invalid' and 'required' keys
  that set up what message to show to the user in case of errors.
* **validators** is a list of dictionaries, each dictionary should at least
  have *expr* key, under that key either some
  `YAQL <https://git.openstack.org/cgit/openstack/yaql/tree/README.rst>`_
  expression is stored, either one-element dictionary with *regexpValidator*
  key (and some regexp string as value).
  Another possible key of a validator dictionary is *message*, and although
  it is not required, it is highly desirable to specify it - otherwise, when
  validator fails (i.e. regexp doesn't match or YAQL expression evaluates to
  false) no message will be shown. Note that field-level validators use YAQL
  context different from all other attributes and section: here *$* root object
  is set to the value of field being validated (to make expressions shorter).

    .. code-block:: yaml

     - name: someField
       type: string
       label: Domain Name
       validators:
         - expr:
             regexpValidator: '(^[^.]+$|^[^.]{1,15}\..*$)'
           message: >-
                NetBIOS name cannot be shorter than 1 symbol and
                longer than 15 symbols.
         - expr:
            regexpValidator: '(^[^.]+$|^[^.]*\.[^.]{2,63}.*$)'
          message: >-
            DNS host name cannot be shorter than 2 symbols and
            longer than 63 symbols.
       helpText: >-
         Just letters, numbers and dashes are allowed.
         A dot can be used to create subdomains

  Using of *regexpValidator* and *validators* attributes with *password*
  field was introduced in version 2.3. By default, password should have at
  least 7 characters, 1 capital letter, 1 non-capital letter, 1 digit, and 1
  special character. If you do not want password validation to be so strong,
  you can override it by setting a custom validator or multiple validators for
  password. For that add *regexpValidator* or *validators* to the *password*
  field and specify custom regexp string as value, just like with any *string*
  field.

  *Example*

  .. code-block:: yaml

     - name: password
       type: password
       label: Password
       descriptionTitle: Password
          description: >-
            Please, provide password for the application. Password should be
             5-50 characters long and consist of alphanumeric characters
       regexpValidator: '^[a-zA-Z0-9]{5,50}?$'

* **confirmInput** is a flag used only with password field and defaults to
  ``true``. If you decided to turn off automatic password field cloning, you
  should set it to ``false``. In this case password confirmation is not
  required from a user.

* **widgetMedia** sets some custom *CSS* and *JavaScript* used for the field's
  widget rendering. Note, that files should be placed to Django static folder
  in advance. Mostly they are used to do some client-side field
  enabling/disabling, hiding/unhiding etc.

* **requirements** is used only with flavor field and prevents user to pick
  unstable for a deployment flavor.
  It allows to set minimum ram (in MBs), disk space (in GBs) or virtual CPU
  quantity.

  Example that shows how to hide items smaller than regular *small* flavor
  in a flavor select field:

  .. code-block:: yaml

   - name: flavor
          type: flavor
          label: Instance flavor
          requirements:
              min_disk: 20
              min_vcpus: 2
              min_memory_mb: 2048

* **include_snapshots** is used only with the volume field. ``True`` by default.
  If ``True``, the field list includes available volumes and volume snapshots.
  If set to ``False``, only available volumes are shown.

* **include_subnets** is used only with network field. ``True`` by default.
  If ``True``, the field list includes all the possible combinations of network
  and subnet. E.g. if there are two available networks X and Y, and X has two
  subnets A and B, while Y has a single subnet C, then the list will include 3
  items: (X, A), (X, B), (Y, C). If set to ``False`` only network names will be
  listed, without their subnets.

* **filter** is used only with network field. ``None`` by default. If set to a
  regexp string, will be used to display only the networks with names matching
  the given regexp.

* **murano_networks** is used only with network field. ``None`` by default. May
  have values ``None``, ``exclude`` or ``translate``. Defines the handling of
  networks which are created by murano.
  Such networks usually have very long randomly generated names, and thus look
  ugly when displayed in the list. If this value is set to ``exclude`` then these
  networks are not shown in the list at all. If set to ``translate`` the
  names of such networks are replaced by a string ``Network of %env_name%``.

  .. note::
     This functionality is based on the simple string matching of the
     network name prefix and the names of all the accessible murano
     environments. If the environment is renamed after the initial deployment
     this feature will not be able to properly translate or exclude its network
     name.

* **allow_auto** is used only with network field. ``True`` by default. Defines if
  the default value of the dropdown (labeled "Auto") should be present in the
  list. The default value is a tuple consisting of two ``None`` values. The logic
  on how to treat this value is up to application developer. It is suggested to
  use this field to indicate that the instance should join default environment
  network. For use-cases where such behavior is not desired, this parameter
  should be set to ``False``.

*Network* field and its specific attributes (*include_subnets*, *filter*,
*murano_networks*, *allow_auto*) are available since version 2.1.
Before that, there was no way for the end user to select existing network in
the UI. The only way to change the default networking behavior was the usage
of networking.yaml file. It allows to override the networking setting at
the environment level, for all the murano environments of all the tenants.
Now you can simple add a *network* field to your form definition and provide
the ability to select the desired network for the specific application.

*Example*

.. code-block:: yaml

  - instanceConfiguration:
      fields:
        - name: network
          type: network
          label: Network
          description: Select a network to join. 'Auto' corresponds to a default environment's network.
          murano_networks: translate

Besides field-level validators, form-level validators also exist. They
use **standard context** for YAQL evaluation and are required when
there is a need to validate some form's constraint across several
fields.

*Example*

.. code-block:: yaml

 Forms:
   - appConfiguration:
       fields:
         - name: dcInstances
           type: integer
           hidden: true
           initial: 1
           required: false
           maxLength: 15
           helpText: Optional field for a machine hostname template
         - name: unitNamingPattern
           type: string
           label: Instance Naming Pattern
           required: false
           maxLength: 64
           regexpValidator: '^[a-zA-Z][-_\w]*$'
           errorMessages:
            invalid: Just letters, numbers, underscores and hyphens are allowed.
          helpText: Just letters, numbers, underscores and hyphens are allowed.
          description: >-
            Specify a string that will be used in a hostname instance.
            Just A-Z, a-z, 0-9, dash, and underline are allowed.


   - instanceConfiguration:
         fields:
           - name: title
             type: string
             required: false
             hidden: true
             descriptionTitle: Instance Configuration
             description: Specify some instance parameters based on which service will be created.
           - name: flavor
             type: flavor
             label: Instance flavor
             description: >-
               Select a flavor registered in OpenStack. Consider that service performance
               depends on this parameter.
             required: false
           - name: osImage
             type: image
             imageType: windows
             label: Instance image
             description: >-
               Select valid image for a service. Image should already be prepared and
               registered in glance.
           - name: availabilityZone
             type: azone
             label: Availability zone
             description: Select an availability zone, where service will be installed.
             required: false
     validators:
        # if unitNamingPattern is given and dcInstances > 1, then '#' should occur in unitNamingPattern
        - expr: $.appConfiguration.dcInstances < 2 or not $.appConfiguration.unitNamingPattern.bool()
                or '#' in $.appConfiguration.unitNamingPattern
          message: Incrementation symbol "#" is required in the Instance Naming Pattern

Control attributes might be initialized with a YAQL expression. However prior
to version 2.4 it only worked for forms other than the first. It was designed
to initialize controls with values input on the previous step. Starting with
version 2.4 this limitation was removed and it become possible to use
arbitrary YAQL expressions for any of control fields on any forms and use
parameter values as part of these expressions.
