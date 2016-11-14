.. _murano-bundles:

==============
Murano bundles
==============

A bundle is a collection of packages. In the Community App Catalog, you can find
such bundles as ``container-based-apps``, ``app-servers``, and so on.
The packages in the Application Catalog are sorted by usage. You can import
bundles from the catalog using Dashboard or CLI. You can read about this in
:ref:`Managing applications <manage_applications>` and :ref:`Using CLI <use-cli>`.
Specific information about *bundle-import* command can be found at
:ref:`Murano command-line client <cli-ref>`.

Bundle structure
~~~~~~~~~~~~~~~~

Bundle description is a JSON structure, that contains list of packages
in the bundle and bundle version. Here is the example:

    .. code-block:: javascript

       {
           "Packages": [
               {
                   "Name": "com.example.apache.ApacheHttpServer",
                   "Version": ""
               },
               {
                   "Name": "com.example.apache.Tomcat",
                   "Version": ""
               }
           ],
           "Version": 1
       }

    ..

``Name`` is a required parameter and should contain package fully qualified name.
``Version``     is not a mandatory parameter. Version for package entry specifies the
version of the package to look into :ref:`Murano package repository <repository>`.
If it is specified, murano client would look for a file with that version
specification in murano repository (for example ``com.example.MyApp.0.0.1.zip``
for com.example.MyApp of version 0.0.1). If the version is omitted or left
blank client would search for ``com.example.MyApp.zip``.

Create local bundle
~~~~~~~~~~~~~~~~~~~

However, you may need to create a local bundle. You may need it if you want to
setup your own :ref:`Murano package repository <repository>`. To create a new
bundle, perform the following steps:

   #. Navigate to the directory with the target packages.

   #. Create a ``.bundle`` file. List all the required packages in ``Packages``
      section. If needed, specify the bundle version in the ``Version`` section.
