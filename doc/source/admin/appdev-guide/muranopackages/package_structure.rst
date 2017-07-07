.. _package_structure:

Package structure
~~~~~~~~~~~~~~~~~

The structure of the Murano application package is predefined. An
application could be successfully uploaded to an application catalog.

The application package root folder should contain the following:

**manifest.yaml** file
 is an application entry point.

 .. note:: the filename is fixed, do not use any custom names.

**Classes** folder
 contains MuranoPL class definitions.

**Resources** folder
 contains execution plan templates and the **scripts**
 folder with all the files required for an application
 deployment located in it.

**UI** folder
 contains the dynamic UI YAML definitions.

**logo.png** file (optional)
 is an image file associated to your application.

 .. note::
    There are no any special limitations regarding an image filename.
    Though, if it differs from the default ``logo.png``, specify it
    in an application manifest file.

**images.lst** file (optional)
  contains a list of images required by an application.

Here is the visual representation of the Murano application
package structure:

.. image:: ../figures/structure.png
