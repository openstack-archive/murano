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

#. In horizon, navigate to Murano > Manage > Package Definitions.
#. Click the **Import Package** button on the top right of the page.

   .. image:: figures/import_package.png
      :alt: Package Definitions page: Import Package 1
      :width: 630 px

#. From the **Package source** drop-down list choose **File**, then
   click **Browse** to select a .zip file you want to import, and
   then click **Next**.

   .. image:: figures/browse_zip_file.png
      :alt: Import Package dialog: zip file
      :width: 630 px

#. At this step, the package is already uploaded. If necessary,
   verify and update the information about the package, then
   click **Next**.
#. Optional: choose one or multiple categories from
   the **Application Category** menu and click the **Create** button.

.. note::
  Though specifying a category is optional, we recommend that you
  specify at least one. It helps to filter applications in the
  catalog.

| A message `Success: Package parameters successfully updated.`
  appears at the top right corner when the application is successfully
  downloaded.

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

#. In horizon, navigate to Murano > Manage > Package Definitions.
#. Click the **Import Package** button on the top right of the page.

   .. image:: figures/import_package.png
      :alt: Package Definitions page: Import Package 2
      :width: 630 px

#. From the **Package source** drop-down list, choose **Repository**,
   enter the package name, and then click **Next**. Note that you may
   also specify the version of the package.

   .. image:: figures/repository.png
      :alt: Import Package dialog: Repository
      :width: 630 px

#. At this step, the package is already uploaded. If necessary,
   verify and update the information about the package, then
   click **Next**.
#. Choose one or multiple categories from the **Application Category**
   menu, then click **Create**.

.. _ui_bundles:

From a bundle of applications
-----------------------------

Perform the following steps to import a bundle of applications:

.. note::
  To import an application bundle from a repository, you need
  to know the full name of the package bundle. To find it out, go
  to http://apps.openstack.org/#tab=murano-apps and click on the
  desired bundle to see its full name.

#. In horizon, navigate to Murano > Manage > Package Definitions.
#. Click the **Import Bundle** button on the top right of the page.

   .. image:: figures/import_bundle.png
      :alt: Package Definitions page: Import Bundle
      :width: 630 px

#. From the **Package Bundle Source** drop-down list, choose
   **Repository**, enter the bundle name, and then click **Create**.

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
  applications

* the bottom section contains all the available applications sorted
  alphabetically

To view all the applications of a specific category, select it from
the **App Category** drop-down list:

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

Delete an application
~~~~~~~~~~~~~~~~~~~~~

Deploy an application
~~~~~~~~~~~~~~~~~~~~~

Show an application topology
----------------------------

Show a deployment log location
------------------------------
