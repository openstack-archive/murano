.. _manage_applications:

=====================
Managing applications
=====================

In murano, each application, as well as the form of application data entry,
is defined by its package. The murano dashboard allows you to import and
manage packages as well as search, filter, and add applications from catalog
to environments.

This section provides detailed instructions on how to import application
packages into murano and then add applications to an environment and deploy
it. This section also shows you how to find component details, application
topology, and deployment logs.

Import an application package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several ways of importing an application package into
murano:

* :ref:`from a zip file <ui_zip>`
* :ref:`from murano applications repository <ui_repo>`
* :ref:`from bundles of applications <ui_bundles>`

.. _ui_zip:

From a zip file
---------------

Perform the following steps to import an application package from a
.zip file:

#. In OpenStack dashboard, navigate to
   :menuselection:`Applications > Manage > Packages`.
#. Click the :guilabel:`Import Package` button on the top right of the
   page.

   .. image:: ../figures/import_package.png
      :alt: Packages page: Import Package 1
      :width: 630 px

#. From the :guilabel:`Package source` drop-down list
   choose :guilabel:`File`, then click :guilabel:`Browse` to select a
   .zip file you want to import, and then click :guilabel:`Next`.

   .. image:: ../figures/browse_zip_file.png
      :alt: Import Package dialog: zip file
      :width: 630 px

#. At this step, the package is already uploaded. Choose a category
   from the :guilabel:`Application Category` menu. You can select
   multiple categories while holding down the :kbd:`Ctrl` key. If
   necessary, verify and update the information about the package,
   then click the :guilabel:`Create` button.

   .. image:: ../figures/add_pkg_info.png
      :alt: Import Package dialog: Description
      :width: 630 px

.. note::
  Though specifying a category is optional, we recommend that you
  specify at least one. It helps to filter applications in the
  catalog.

| Green messages appear at the top right corner when the application
  is successfully uploaded. In case of a failure, you will see a red
  message with the problem description. For more information, please
  refer to the logs.


.. _ui_repo:

From a repository
-----------------

Perform the following steps to import an application package from
murano applications repository:

.. note::
  To import an application package from a repository, you need to
  know the full name of the package. For the packages names, go to
  http://apps.openstack.org/#tab=murano-apps and click on the desired
  package to see its full name.

#. In OpenStack dashboard, navigate to
   :menuselection:`Applications > Manage > Packages`.

#. Click the :guilabel:`Import Package` button on the top right of the
   page.

   .. image:: ../figures/import_package.png
      :alt: Packages page: Import Package 2
      :width: 630 px

#. From the :guilabel:`Package source` drop-down list,
   choose :guilabel:`Repository`, enter the package name, and then
   click :guilabel:`Next`. Note that you may also specify the version
   of the package.

   .. image:: ../figures/repository.png
      :alt: Import Package dialog: Repository
      :width: 630 px

#. At this step, the package is already uploaded. Choose a category
   from the :guilabel:`Application Category` menu. You can select
   multiple categories while holding down the :kbd:`Ctrl` key. If
   necessary, verify and update the information about the package,
   then click the :guilabel:`Create` button.

   .. image:: ../figures/add_pkg_info.png
      :alt: Import Package dialog: Description
      :width: 630 px

.. _ui_bundles:

From a bundle of applications
-----------------------------

Perform the following steps to import a bundle of applications:

.. note::
  To import an application bundle from a repository, you need
  to know the full name of the package bundle. To find it out, go
  to http://apps.openstack.org/#tab=murano-apps and click on the
  desired bundle to see its full name.

#. In OpenStack dashboard, navigate to
   :menuselection:`Applications > Manage > Packages`.

#. Click the :guilabel:`Import Bundle` button on the top right of the
   page.

   .. image:: ../figures/import_bundle.png
      :alt: Packages page: Import Bundle
      :width: 630 px

#. From the :guilabel:`Package Bundle Source` drop-down list, choose
   :guilabel:`Repository`, enter the bundle name, and then
   click :guilabel:`Create`.

   .. image:: ../figures/bundle_name.png
      :alt: Import Bundle dialog
      :width: 630 px

Search for an application in the catalog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you have imported many applications and want to quickly find
a required one, you can filter them by category, tags and words that
the application name or description contains:

In OpenStack dashboard, navigate to :menuselection:`Applications > Catalog
> Browse`.

The page is divided into two sections:

* **Recent Activity** shows the most recently imported or deployed
  applications.

* The bottom section contains all the available applications sorted
  alphabetically.

To view all the applications of a specific category, select it from
the :guilabel:`App Category` drop-down list:

  .. image:: ../figures/app_category.png
     :alt: Applications page: App Category
     :width: 630 px

To filter applications by tags or words from the application name or
description, use the rightmost filter:

  .. image:: ../figures/app_filter.png
     :alt: Applications page: Filter
     :width: 630 px

.. note::

   Tags can be specified during the import of an application package.

For example, there is an application that has the word
*document-oriented* in description. Let's find it with the filter.
The following screenshot shows you the result.

 .. image:: ../figures/app_filter_example.png
    :alt: Applications page: example
    :width: 630 px

Delete an application package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To delete an application package from the catalog, please perform
the following steps:

#. In OpenStack dashboard, navigate to :menuselection:`Applications > Manage > Packages`.

#. Select a package or multiple packages you want to delete and click
   :guilabel:`Delete Packages`.

   .. image:: ../figures/select_packages.png
      :alt: Packages page: Select packages
      :width: 630 px

#. Confirm the deletion.

Add an application to environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After uploading an application, the second step is to add it to an
environment. You can do this:

* :ref:`from environment details page <from_env>`
* :ref:`from applications catalog page <from_cat>`

.. _from_env:

From environment details page
-----------------------------

#. In OpenStack dashboard, navigate to
   :menuselection:`Applications > Catalog > Environments`.

#. Find the environment you want to manage and click
   :guilabel:`Manage Components`, or simply click on the environment's
   name.

#. Procced with the :ref:`Drop Components here <drag_and_drop>` field
   or the :ref:`Add Component <add_component>` button.

.. _drag_and_drop:

**Use of Drop Components here field**

#. On the Environment Components page, drag and drop a desired
   application into the :guilabel:`Drop Components here` field under
   the :guilabel:`Application Components` section.

   .. image:: ../figures/add_to_env/drag_and_drop.png
      :alt: Environment Components page: Drag and drop a component
      :width: 630 px

#. Configure the application. Note that the settings may vary from app to app
   and are predefined by the application author. When done, click
   :guilabel:`Next`, then click :guilabel:`Create`.

Now the application appears in the :guilabel:`Component List` section on
the Environment Components page.

.. _add_component:

**Use of Add Component button**

#. On the Environment Components page, click :guilabel:`Add Component`.

   .. image:: ../figures/add_to_env/add_component.png
      :alt: Environment Components page: Add component
      :width: 630 px

#. Find the application you want to add and click :guilabel:`Add to Env`.

   .. image:: ../figures/add_to_env/add_to_env.png
      :alt: Applications page: Add to Env
      :width: 630 px

#. Configure the application and click :guilabel:`Next`. Note that the
   settings may vary from app to app and are predefined by the
   application author.

#. To add more applications, check :guilabel:`Continue application adding`,
   then click :guilabel:`Create` and repeat the steps above. Otherwise, just
   click :guilabel:`Create`.

   .. image:: ../figures/add_to_env/add_more_apps.png
      :alt: Configure Application dialog: Add more applications
      :width: 630 px

   Now the application appears in the :guilabel:`Component List` section
   on the Environment Components page.

.. _from_cat:

From applications catalog page
------------------------------

#. In OpenStack dashboard, navigate to
   :menuselection:`Applications > Catalog > Browse`.

#. On the Applications catalog page, use one of the following methods:

   * `Quick deploy`_. Automatically creates an
     environment, adds the selected application, and redirects you
     to the page with the environment components.
   * `Add to Env`_. Adds an application to an already
     existing environment.

.. _Quick deploy:

**Quick Deploy button**

#. Find the application you want to add and click
   :guilabel:`Quick Deploy`. Let's add Apache Tomcat, for example.

   .. image:: ../figures/add_to_env/quick_deploy.png
      :alt: Applications page: Quick Deploy
      :width: 630 px


#. Configure the application. Note that the settings may vary from app to
   app and are predefined by the application author. When done, click
   :guilabel:`Next`, then click :guilabel:`Create`. In the example
   below we assign a floating IP address.

   .. image:: ../figures/add_to_env/configure_app.png
      :alt: Configure Application dialog
      :width: 630 px

Now the Apache Tomcat application is successfully added to an
automatically created ``quick-env-1`` environment.

   .. image:: ../figures/add_to_env/quick_env.png
      :alt: Environment Components page: Select packages
      :width: 630 px

.. _Add to Env:

**Add to Env button**

#. From the :guilabel:`Environment` drop-down list, select the
   required environment.

   .. image:: ../figures/add_to_env/add_from_cat.png
      :alt: Applications page: Select environment
      :width: 630 px

#. Find the application you want to add and click
   :guilabel:`Add to Env`. Let's add Apache Tomcat, for example.

   .. image:: ../figures/add_to_env/add_to_env.png
      :alt: Applications page: Add to Env
      :width: 630 px

#. Configure the application and click :guilabel:`Next`. Note that the
   settings may vary from app to app and are predefined by the
   application author. In the example below we assign a floating
   IP address.

   .. image:: ../figures/add_to_env/configure_app.png
      :alt: Configure Application dialog
      :width: 630 px

#. To add more applications, check :guilabel:`Add more applications
   to the environment`, then click :guilabel:`Create` and repeat the
   steps above. Otherwise, just click :guilabel:`Create`.

   .. image:: ../figures/add_to_env/add_more_apps.png
      :alt: Configure Application dialog: Add more applications
      :width: 630 px

Deploy an environment
~~~~~~~~~~~~~~~~~~~~~

Make sure to add necessary applications to your environment, then deploy it
following one of the options below:

* Deploy an environment from the Environments page

  #. In OpenStack dashboard, navigate to :menuselection:`Applications >
     Catalog > Environments`.

  #. Select :guilabel:`Deploy Environment` from the Actions drop-down list
     next to the environment you want to deploy.

     .. image:: ../figures/deploy_env_2.png
        :width: 630 px
        :alt: Environments page

     It may take some time for the environment to deploy. Wait for the status
     to change from `Deploying` to `Ready`. You cannot add applications to
     your environment during deployment.

* Deploy an environment from the Environment Components page

  #. In OpenStack dashboard, navigate to :menuselection:`Applications >
     Catalog > Environments`.

  #. Click the name of the environment you want to deploy.

     .. image:: ../figures/environments.png
        :width: 630 px
        :alt: Environments page

  #. On the Environment Components page, click :guilabel:`Deploy This Environment`
     to start the deployment.

     .. image:: ../figures/deploy_env.png
        :width: 630 px
        :alt: Environment Components page

     It may take some time for the environment to deploy. You cannot add
     applications to your environment during deployment. Wait for the status
     to change from `Deploying` to `Ready`. You can check the status either on
     the Environments page or on the Environment Components page.

.. _component-details:

Browse component details
------------------------

You can browse component details to find the following information about
a component:

* Name
* ID
* Type
* Instance name (available only after deployment)
* Heat orchestration stack name (available only after deployment)

To browse a component details, perform the following steps:

#. In OpenStack dashboard, navigate to
   :menuselection:`Applications > Catalog > Environments`.

#. Click the name of the required environment.

#. In the :guilabel:`Component List` section, click the name of the required
   component.

   .. image:: ../figures/component-details.png
      :width: 630 px
      :alt: Components details

   The links redirect to corresponding horizon pages with the detailed
   information on instance and heat stack.

.. _application-topology:

Application topology
--------------------

Once you add an application to your environment, the application topology of
this environment becomes available in a separate tab. The topology represents
an elastic diagram showing the relationship between a component and the
infrastructure it runs on. To view the topology:

#. In OpenStack dashboard, navigate to
   :menuselection:`Applications > Catalog > Environments`.

#. Click the name of the necessary environment.

#. Click the :guilabel:`Topology` tab.

The topology is helpful to visually display complex components, for example
Kubernetes. The red icons reflect errors during the deployment while the green
ones show success.

.. image:: ../figures/topology_kubernetes.png
   :alt: Topology tab: Deployment failed
   :width: 630 px

The following elements of the topology are virtual machine and an instance of
dependent MuranoPL class:

+---------------------------------------------+----------------------------+
| Element                                     | Meaning                    |
+=============================================+============================+
| .. image:: ../figures/topology_element_1.png| Virtual machine            |
+---------------------------------------------+----------------------------+
| .. image:: ../figures/topology_element_2.png| Instance                   |
+---------------------------------------------+----------------------------+

Position your mouse pointer over an element to see its name, ID, and other
details.

.. image:: ../figures/topology_wordpress.png
   :alt: Topology tab: Deployment successful
   :width: 630 px


Deployment logs
---------------

To get detailed information on a deployment, use:

* :ref:`Deployment history <depl-history>`, which contains logs and deployment
  structure of an environment.

* :ref:`Latest deployment log <latest-log>`, which contains information on the
  latest deployment of an environment.

* :ref:`Component logs <component-logs>`, which contain logs on a particular
  component in an environment.

.. _depl-history:

**Deployment history**

To see the log of a particular deployment, proceed with the steps
below:

#. In OpenStack dashboard, navigate to :menuselection:`Applications > Catalog >
   Environments`.

#. Click the name of the required environment.

#. Click the :guilabel:`Deployment History` tab.

#. Find the required deployment and click :guilabel:`Show Details`.

#. Click the :guilabel:`Logs` tab to see the logs.

   .. image:: ../figures/logs.png
      :alt: Deployment Logs page
      :width: 630 px

.. _latest-log:

**Latest deployment log**

To see the latest deployment log, proceed with the steps below:

#. In OpenStack dashboard, navigate to :menuselection:`Applications > Catalog >
   Environments`.

#. Click the name of the required environment.

#. Click the :guilabel:`Latest Deployment Log` tab to see the logs.

.. _component-logs:

**Component logs**

To see the logs of a particular component of an environment, proceed with the
steps below:

#. In OpenStack dashboard, navigate to :menuselection:`Applications > Catalog >
   Environments`.

#. Click the name of the required environment.

#. In the :guilabel:`Component List` section, click the required component.

#. Click the :guilabel:`Logs` tab to see the component logs.

   .. image:: ../figures/env-component-logs.png
      :alt: Component Logs page
      :width: 630 px

Delete an application
~~~~~~~~~~~~~~~~~~~~~

To delete an application that belongs to the environment:

#. In OpenStack dashboard, navigate to :menuselection:`Applications >
   Catalog > Environments`.

#. Click on the name of the environment you want to delete an
   application from.

   .. image:: ../figures/environments.png
      :width: 630 px
      :alt: Environments page

#. In the :guilabel:`Component List` section, click the
   :guilabel:`Delete Component` button next to the application you
   want to delete. Then confirm the deletion.

   .. image:: ../figures/delete_application.png
      :width: 630 px
      :alt: Environment Components page

.. note::
   If the application that you are deleting has already been deployed,
   you should redeploy the environment to apply the recent changes.
   If the environment has not been deployed with this component,
   the changes are applied immediately on receiving the confirmation.

.. warning::
   Due to a known bug in murano as of Kilo release, the OS resources
   allocated by a deleted application might not be reclaimed until
   you delete the environment. See the `Deallocating stack resources
   <https://blueprints.launchpad.net/murano/+spec/deallocating-stack-resources>`_
   blueprint for details.
