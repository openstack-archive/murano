.. _app-debugging:

================================
Application developer's cookbook
================================

If you have not written murano packages before,
start from the existing :ref:`Step-by-Step <step-by-step>` guide. It contains
general information about murano packages development process. Additionally,
see the :ref:`MuranoPL reference <murano-pl>`.

Load applications from a local directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Normally, whenever you make changes to your application, you have to package it,
re-upload the package to the API, and delete the old package from the API. This
makes developing and testing murano applications troublesome and time-consuming.
Murano-engine provides a way to speed up the edit-upload-deploy loop. This can be
done with the ``load_packages_from`` option. Murano-engine examines any directories
mentioned in this option before accessing the API. Therefore, you do not even
need to package the application into a ZIP archive and any changes you make are
instantly available to the engine, if you do not plan to check or change the
application UI. To check your application's appearance in the OpenStack dashboard,
upload the application for the first run. Additionally, re-upload the package
using the OpenStack dashboard or CLI each time you update the application UI.

To load an application from a local directory, modify
the ``load_packages_from`` parameter in murano config ``[engine]`` section.

.. code-block:: console

   [engine]
   ...
   load_packages_from = /path/to/murano/applications
   ...

.. note::
   The murano-engine scans the directory structure and seeks application
   manifests. Therefore, you can point the ``load_packages_from`` parameter
   to a cloned version of the murano-apps repository.

Deploy environment using CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The standard way to deploy an application in murano is by using the murano
dashboard (OpenStack dashboard plug-in). However, if the OpenStack dashboard is
not available or some sort of automation is required, murano provides the
capability to deploy environments through CLI. It is a powerful tool
that allows users and application developers make arbitrary changes to apps
object-model. This can be useful in early stages of application development to
experiment with different object models of an application. You can read more about
it in :ref:`Deploying environments using CLI <deploying-using-cli>`

Application unit test framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An application unit test framework was created to make development process
easier. With this framework you can check different scenarios of application
deployment without running real deployments.

For more information about application unit tests, see
:ref:`Application unit tests <app-unit-tests>`.
