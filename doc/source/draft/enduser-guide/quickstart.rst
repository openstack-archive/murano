.. _quickstart:

==========
Quickstart
==========

This is a brief walkthrough to quickly get you familiar with the basic
operations you can perform when using the Application catalog directly
from the dashboard.

For the detailed instructions on how to :ref:`manage your environments
<manage-environments>` and :ref:`applications <manage_applications>`,
please proceed with dedicated sections.


Upload an application
~~~~~~~~~~~~~~~~~~~~~

#. Log in to the OpenStack dashboard.

#. Navigate to :menuselection:`Murano > Manage > Package Definitions`.

#. Click the :guilabel:`Import Package` button:

   .. image:: figures/qs_package_import.png
      :alt: Package Definitions page
      :width: 600 px

#. In the :guilabel:`Import Package` dialog:

   * Select ``URL`` from the ``Package Source`` drop-down list;

   * Specify the URL in the :guilabel:`Package URL` field. Lets upload
     the Apache HTTP Server package using
     http://storage.apps.openstack.org/apps/io.murano.apps.apache.ApacheHttpServer.zip;

   * Click :guilabel:`Next` to continue:

   .. image:: figures/qs_package_url.png
      :width: 600 px
      :alt: Import Package dialog 1

#. View the package details in the new dialog, click :guilabel:`Next`
   to continue:

   .. image:: figures/qs_package_details.png
      :width: 600 px
      :alt: Import Package dialog 2

#. Select the :guilabel:`Application Servers` from the application category list,
   click :guilabel:`Create` to import the application package:

   .. image:: figures/qs_app_category.png
      :width: 600 px
      :alt: Import Package dialog 3

#. Now your application is available from :menuselection:`Murano >
   Applcation Catalog > Applications` page.


Deploy an application
~~~~~~~~~~~~~~~~~~~~~

#. Log in to the OpenStack dashboard.

#. Navigate to :menuselection:`Murano > Application Catalog > Applications`.

#. Click on the :guilabel:`Quick Deploy` button from the required application
   from the list. Lets deploy Apache HTTP Server, for example:

   .. image:: figures/qs_apps.png
      :width: 600 px
      :alt: Applications page

#. Check :guilabel:`Assign Floating IP` and click :guilabel:`Next` to proceed:

   .. image:: figures/qs_quick_deploy.png
      :width: 600 px
      :alt: Configure Application dialog 1

#. Select the :guilabel:`Instance Image` from the drop-down list and click
   :guilabel:`Create`:

   .. image:: figures/qs_quick_deploy_2.png
      :width: 600 px
      :alt: Configure Application dialog 2

#. Now the Apache HTTP Server application is successfully added to the newly
   created ``quick-env-1`` environment. Click the :guilabel:`Deploy This Environment`
   button to start the deployment:

   .. image:: figures/qs_quick_env.png
      :width: 600 px
      :alt: Environment "quick-env-1" page

   It may take some time for the environment to deploy. Wait until the status
   is changed from ``Deploying`` to ``Ready``.

#. Navigate to `Murano > Application Catalog > Environments` to view the
   details.


Reconfigure an application
~~~~~~~~~~~~~~~~~~~~~~~~~~


Delete an application
~~~~~~~~~~~~~~~~~~~~~
