..
      Copyright 2015 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http//www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _repository:

=========================
Murano package repository
=========================

Murano client and dashboard are both capable of installing packages and
bundles of packages from murano repository. To do so you should set
``MURANO_REPO_URL`` settings in murano dashboard or ``MURANO_REPO_URL`` env
variable for the CLI client and use the respective command for package import.
These commands would then automatically import all the prerequisites for the
app being installed along with any images, mentioned in said apps.

For more info about importing from repository see :ref:`client`.

Setting up your own repository
==============================

It's fairly easy to set up your own murano package repository.
To do so you need a web server, that would serve 3 directories:
    * /apps/
    * /bundles/
    * /images/

When importing an app by name client would append any version info, if present
to the app name, ``.zip`` file extension and search for that file in the
``apps`` directory.

When importing a bundle by name client would append ``.bundle`` file
extension to the bundle name and search it in the ``bundles`` directory.
Bundle file is a json or a yaml file with the following structure:

.. code-block:: json

    {"Packages":
        [
            {"Name": "io.murano.apps.ApacheHttpServer"},
            {"Version": "", "Name": "io.murano.apps.Nginx"},
            {"Version": "0.0.1", "Name": "io.murano.apps.Lighttpd"}
        ]
    }

Glance images can be auto-imported by client, when mentioned in ``images.lst``
inside the package. Please see :ref:`app_pkg` for more info about pakcage
composition.
When importing images from ``image.lst`` file client simply searches for a
file with the same name as the ``Name`` attribute of the image in the
``images`` directory of the repository.
