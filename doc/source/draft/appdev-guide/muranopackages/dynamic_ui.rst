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

Application and Templates
-------------------------

The Application section describes an *application object model*.
This model will be translated into json, and an application will be
deployed according to that json. The application section should
contain all necessary keys that are required by the murano-engine to
deploy an application. Note that the system section of the object model goes
under the *?*. So murano recognizes that instead of simple value,
MuranoPL object is used. You can pick parameters you got from a user
(they should be described in the Forms section) and pick the right place
where they should be set. To do this `YAQL
<https://git.openstack.org/cgit/openstack/yaql/tree/README.rst>`_ is
used. Below is an example of how two YAQL functions are used for object model
generation:

* **generateHostname** is used for a machine hostname template generation;
  it accepts two arguments: name pattern (string) and index (integer). If '#'
  symbol is present in name pattern, it will be replaced with the index
  provided. If pattern is not given, a random name will be generated.
* **repeat** is used to produce a list of data snippets, given the template
  snippet (first argument) and number of times it should be reproduced (second
  argument). Inside that template snippet current step can be referenced as
  *$index*.

.. note::
   While evaluating YAQL expressions referenced from
   **Application** section (as well as almost all attributes inside
   **Forms** section, see later), *$* root object is set to the list of
   dictionaries with cleaned validated forms' data. For example, to obtain
   a cleaned value of field *name* of form *appConfiguration* , you should reference it
   as *$.appConfiguration.name*. This context will be called as a
   **standard context** throughout the text.

*Example:*

.. code-block:: yaml

   Templates:
     primaryController:
        ?:
          type: io.murano.windows.activeDirectory.PrimaryController
        host:
          ?:
            type: io.murano.windows.Host
          adminPassword: $.appConfiguration.adminPassword
          name: generateHostname($.appConfiguration.unitNamingPattern, 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage

      secondaryController:
        ?:
          type: io.murano.windows.activeDirectory.SecondaryController
        host:
          ?:
            type: io.murano.windows.Host
          adminPassword: $.appConfiguration.adminPassword
          name: generateHostname($.appConfiguration.unitNamingPattern, $index + 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage

   Application:
     ?:
       type: io.murano.windows.activeDirectory.ActiveDirectory
     primaryController: $primaryController
     secondaryControllers: repeat($secondaryController, $.appConfiguration.dcInstances - 1)


Forms
-----

This section describes markup elements for defining forms, which are currently
rendered and validated with Django. Each form has a name, field definitions
(mandatory), and validator definitions (optionally).

Note that each form is splitted into 2 parts:

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
  Use yaml line folding character ``>-`` to keep the correct formatting during
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

