.. _repository:

Murano package repository
~~~~~~~~~~~~~~~~~~~~~~~~~

Murano client and dashboard can install both packages and bundles of packages from murano repository. To do so you should set MURANO_REPO_URL settings in murano dashboard or MURANO_REPO_URL env variable for the CLI client, and use a respective command to import the package. These commands automatically import all the prerequisites required to install the application along with any images mentioned in the applications.

Setting up your own repository
------------------------------

It is fairly easy to set up your own murano package repository. To do so you need a web server that would serve 3 directories:
    * /apps/
    * /bundles/
    * /images/

When importing an application by name, the client appends any version info, if present to the application name, ``.zip`` file extension and searches for that file in the ``apps`` directory.

When importing a bundle by name, the client appends ``.bundle`` file extension to the bundle name and searches it in the bundles directory. A bundle file is a JSON or a YAML file with the following structure:

.. code-block:: json

    {"Packages":
        [
            {"Name": "com.example.ApacheHttpServer"},
            {"Version": "", "Name": "com.example.Nginx"},
            {"Version": "0.0.1", "Name": "com.example.Lighttpd"}
        ]
    }

Glance images can be auto-imported by the client, when mentioned in ``images.lst`` inside the package. Please see :ref:`step-by-step` for more information about package composition.
When importing images from the ``image.lst`` file, the client simply searches for a file with the same name as the name attribute of the image in the ``images`` directory of the repository.
