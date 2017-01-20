.. _app_migrate_to_liberty:

Migrate applications to Stable/Liberty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Liberty a number of useful features that can be used by developers creating
their murano applications were implemented. This document describes these
features and steps required to include them to new apps.

1. Versioning
-------------

Package version
```````````````

Now murano packages have a new optional attribute in their manifest called
`Version` - a standard SemVer format version string. All MuranoPL classes have
the version of the package they contained in.
To specify the version of your package, add a new section to the manifest file:

  .. code-block:: yaml

   Version: 0.1.0

  ..

If no version specified, the package version will be equal to *0.0.0*.

Package requirements
````````````````````

There are cases when packages may require other packages for their work.
Now you need to list such packages in the `Require` section of the manifest
file:

  .. code-block:: yaml

   Require:
     package1_FQN: version_spec_1
     ...
     packageN_FQN: version_spec_N

  ..

`version_spec` here denotes the allowed version range. It can be either in
semantic_version specification pip-like format or as partial version string.
If you do not want to specify the package version, leave this value empty:

  .. code-block:: yaml

   Require:
     package1_FQN: '>=0.0.3'
     package2_FQN:

  ..

In this case, the last dependency *0.x.y* is used.


.. note::
   All packages depend on the `io.murano` package (core library). If you do not
   specify this requirement in the list (or the list is empty or even there is
   no `Require` key in package manifest), then dependency *io.murano: 0* will
   be automatically added.


Object version
``````````````
Now you can specify the version of objects in UI definition when your
application requires specific version of some class. To do this, add new key
`classVersion` to section `?` describing object:

  .. code-block:: yaml

   ?:
     type: io.test.apps.TestApp
     classVersion: 0.0.1

  ..

`classVersion` of all classes included to package equals `Version` of this
package.

2. YAQL
-------

In Liberty, murano was updated to use `yaql 1.0.0`.
The new version of YAQL allows you to use a number of new functions and
features that help to increase the speed of developing new applications.

.. note::
   Usage of these features makes your applications incompatible with
   older versions of murano.

Also, in Liberty you can change `Format` in the manifest of package from
*1.0* to *1.1* or *1.2*.

 * **1.0** - supported by all versions of murano.
 * **1.1** - supported by Liberty+. Specify it, if you want to use features
   from *yaql 0.2* and *yaql 1.0.0* at the same time in your application.
 * **1.2** - supported by Liberty+. A number of features from *yaql 0.2* do not
   work with this format (see the list below). We recommend you to use it for
   new applications where compatibility with Kilo is not required.

Some examples of *yaql 0.2* features that are not compatible  with the *1.2* format
```````````````````````````````````````````````````````````````````````````````````

 * Several functions now cannot be called as MuranoObject methods:
   ``id(), cast(), super(), psuper(), type()``.

 * Now you do not have the ability to compare non-comparable types.
   For example "string != false"

 * Dicts are not iterable now, so you cannot do this:
   ``If: $key in $dict``. Use ``$key in $dict.keys()``
   or ``$v in $dict.values()``

 * Tuples are not available. ``=>`` always means keyword argument.

3. Simple software configuration
--------------------------------

Previously, you always had to create execution plans even when some short
scripts had to be executed on a VM. This process included creating a template
file, creating a script, and describing the sending of the execution plan to
the murano agent.

Now you can use a new class **io.murano.configuration.Linux** from murano
`core-library`. This allows sending short commands to the VM and putting files
from the ``Resources`` folder of packages to some path on the VM without the
need of creating execution plans.

To use this feature you need to:

* Declare a namespace (for convenience)

  .. code-block:: yaml

    Namespaces:
      conf: io.murano.configuration
      ...
  ..

* Create object of ``io.murano.configuration.Linux`` class in workflow of
  your application:

  .. code-block:: yaml

    $linux: new(conf:Linux)
  ..

* Run one of the two feature methods: ``runCommand`` or ``putFile``:

  .. code-block:: yaml

    # first argument is agent of instance, second - your command
    $linux.runCommand($.instance.agent, 'service apache2 restart')
  ..

  or:

  .. code-block:: yaml

    # getting content of file from 'Resources' folder
    - $resources: new(sys:Resources)
    - $fileContent: $resources.string('your_file.name')
    # put this content to some directory on VM
    - $linux.putFile($.instance.agent, $fileContent, '/tmp/your_file.name')
  ..


.. note::
   At the moment, you can use this feature only if your app requires an
   instance of ``LinuxMuranoInstance`` type.

4. UI network selection element
-------------------------------

Since Liberty, you can provide users with the ability to choose where to join
their VM: to a new network created during the deployment, or to an already
existing network.
Dynamic UI now has a new type of field - ``NetworkChoiseField``. This field
provides a selection of networks and their subnetworks as a dropdown populated
with those which are available to the current project (tenant).

To use this feature, you should make the following updates in the Dynamic UI of
an application:

* Add ``network`` field:

  .. code-block:: yaml

    fields:
      - name: network
        type: network
        label: Network
        description: Select a network to join. 'Auto' corresponds to a default environment's network.
        required: false
        murano_networks: translate
  ..

  To see the full list of the ``network`` field arguments, refer to the UI
  forms :ref:`specification <DynamicUISpec>`.

* Add template:

  .. code-block:: yaml

    Templates:
      customJoinNet:
        - ?:
            type: io.murano.resources.ExistingNeutronNetwork
          internalNetworkName: $.instanceConfiguration.network[0]
          internalSubnetworkName: $.instanceConfiguration.network[1]
  ..

* Add declaration of `networks` instance property:

  .. code-block:: yaml

    Application:
      ?:
        type: com.example.exampleApp
      instance:
        ?:
          type: io.murano.resources.LinuxMuranoInstance
      networks:
        useEnvironmentNetwork: $.instanceConfiguration.network[0]=null
        useFlatNetwork: false
        customNetworks: switch($.instanceConfiguration.network[0], $=null=>list(), $!=null=>$customJoinNet)

  ..

For more details about this feature, see :ref:`use-cases <use-cases>`

.. note::
   To use this feature, the version of UI definition must be **2.1+**

5. Remove name field from fields and object model in dynamic UI
---------------------------------------------------------------

Previously, each class of an application had a ``name`` property. It had no
built-in predefined meaning for MuranoPL classes and mostly used for dynamic UI
purposes.

Now you can create your applications without this property in classes and
without a corresponding field in UI definitions. The field for app name will be
automatically generated on the last management form before start of deployment.
Bonus of deleting this - to remove unused property from muranopl class that is
needed for dashboard only.

So, to update existing application developer should make 3 steps:

#. remove ``name`` field and property declaration from UI definition;

#. remove ``name`` property from class of application and make sure that it is
   not used anywhere in workflow

#. set version of UI definition to **2.2 or higher**
