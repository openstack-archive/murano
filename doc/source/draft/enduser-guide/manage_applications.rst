.. _manage_applications:

.. toctree::
   :maxdepth: 2

=====================
Managing applications
=====================

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
   :menuselection:`Murano > Manage > Package Definitions`.
#. Click the :guilabel:`Import Package` button on the top right of the
   page.

   .. image:: figures/import_package.png
      :alt: Package Definitions page: Import Package 1
      :width: 630 px

#. From the :guilabel:`Package source` drop-down list
   choose :guilabel:`File`, then click :guilabel:`Browse` to select a
   .zip file you want to import, and then click :guilabel:`Next`.

   .. image:: figures/browse_zip_file.png
      :alt: Import Package dialog: zip file
      :width: 630 px

#. At this step, the package is already uploaded. Choose a category
   from the :guilabel:`Application Category` menu. You can select
   multiple categories while holding down the :kbd:`Ctrl` key. If
   necessary, verify and update the information about the package,
   then click the :guilabel:`Create` button.

   .. image:: figures/add_pkg_info.png
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

#. In dashboard, navigate to
   :menuselection:`Murano > Manage > Package Definitions`.
#. Click the :guilabel:`Import Package` button on the top right of the
   page.

   .. image:: figures/import_package.png
      :alt: Package Definitions page: Import Package 2
      :width: 630 px

#. From the :guilabel:`Package source` drop-down list,
   choose :guilabel:`Repository`, enter the package name, and then
   click :guilabel:`Next`. Note that you may also specify the version
   of the package.

   .. image:: figures/repository.png
      :alt: Import Package dialog: Repository
      :width: 630 px

#. At this step, the package is already uploaded. Choose a category
   from the :guilabel:`Application Category` menu. You can select
   multiple categories while holding down the :kbd:`Ctrl` key. If
   necessary, verify and update the information about the package,
   then click the :guilabel:`Create` button.

   .. image:: figures/add_pkg_info.png
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

#. In dashboard, navigate to
   :menuselection:`Murano > Manage > Package Definitions`.
#. Click the :guilabel:`Import Bundle` button on the top right of the
   page.

   .. image:: figures/import_bundle.png
      :alt: Package Definitions page: Import Bundle
      :width: 630 px

#. From the :guilabel:`Package Bundle Source` drop-down list, choose
   :guilabel:`Repository`, enter the bundle name, and then 
   click :guilabel:`Create`.

   .. image:: figures/bundle_name.png
      :alt: Import Bundle dialog
      :width: 630 px

Search for an application in the catalog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you have imported many applications and want to quickly find
a required one, you can filter them by category, tags and words that
the application name or description contains:

In dashboard, navigate to :menuselection:`Murano > Application Catalog
> Applications`.

The page is divided into two sections:

* **Recent Activity** shows the most recently imported or deployed
  applications.

* The bottom section contains all the available applications sorted
  alphabetically.

To view all the applications of a specific category, select it from
the :guilabel:`App Category` drop-down list:

  .. image:: figures/app_category.png
     :alt: Applications page: App Category
     :width: 630 px

To filter applications by tags or words from the application name or
description, use the rightmost filter:

  .. image:: figures/app_filter.png
     :alt: Applications page: Filter
     :width: 630 px

.. note::

   Tags can be specified during the import of an application package.

For example, there is an application that has the word
*community-developed* in description. Let's find it with the filter.
The following screenshot shows you the result.

 .. image:: figures/app_filter_example.png
    :alt: Applications page: example
    :width: 630 px

Delete an application package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To delete an application package from the catalog, please perform
the following steps:

#. In dashboard, navigate to :menuselection:`Murano > Manage > Package
   Definitions`.

#. Select a package or multiple packages you want to delete and click
   :guilabel:`Delete Packages`.

   .. image:: figures/select_packages.png
      :alt: Package Definitions page: Select packages
      :width: 630 px

#. Confirm the deletion.

Add an application to environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deploy an application
~~~~~~~~~~~~~~~~~~~~~

Show an application topology
----------------------------

Show a deployment log location
------------------------------

Delete an application
~~~~~~~~~~~~~~~~~~~~~

To delete an application that belongs to the environment:

#. In OpenStack dashboard, navigate to :menuselection:`Murano >
   Application Catalog > Environments`.

#. Click on the name of the environment you want to delete an
   application from.

   .. image:: figures/environments.png
      :width: 630 px
      :alt: Environments page

#. In the :guilabel:`Component List` section, click the
   :guilabel:`Delete Component` button next to the application you
   want to delete. Then confirm the deletion.

   .. image:: figures/delete_application.png
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
