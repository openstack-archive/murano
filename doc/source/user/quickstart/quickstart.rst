.. _quickstart:

==========
QuickStart
==========

This is a brief walkthrough to quickly get you familiar with the basic
operations you can perform when using the Application catalog directly
from the dashboard.

For the detailed instructions on how to :ref:`manage your environments
<manage-environments>` and :ref:`applications <manage_applications>`,
please proceed with dedicated sections.


Upload an application
~~~~~~~~~~~~~~~~~~~~~

To upload an application to the catalog:

#. Log in to the OpenStack dashboard.

#. Navigate to :menuselection:`Applications > Manage > Packages`.

#. Click on the :guilabel:`Import Package` button:

   .. image:: ../figures/qs_package_import.png
      :alt: Packages page
      :width: 600 px

#. In the :guilabel:`Import Package` dialog:

   * Select ``URL`` from the ``Package Source`` drop-down list;

   * Specify the URL in the :guilabel:`Package URL` field. Lets upload
     the Apache HTTP Server package using
     http://storage.apps.openstack.org/apps/com.example.apache.ApacheHttpServer.zip;

   * Click :guilabel:`Next` to continue:

   .. image:: ../figures/qs_package_url.png
      :width: 600 px
      :alt: Import Package dialog 1

#. View the package details in the new dialog, click :guilabel:`Next`
   to continue:

   .. image:: ../figures/qs_package_details.png
      :width: 600 px
      :alt: Import Package dialog 2

#. Select the :guilabel:`Application Servers` from the application category list,
   click :guilabel:`Create` to import the application package:

   .. image:: ../figures/qs_app_category.png
      :width: 600 px
      :alt: Import Package dialog 3

#. Now your application is available from :menuselection:`Applications >
   Catalog > Browse` page.


Deploy an application
~~~~~~~~~~~~~~~~~~~~~

To add an application to an environment's component list
and deploy the environment:

#. Log in to the OpenStack dashboard.

#. Navigate to :menuselection:`Applications > Catalog > Browse`.

#. Click on the :guilabel:`Quick Deploy` button from the required application
   from the list. Lets deploy Apache HTTP Server, for example:

   .. image:: ../figures/qs_apps.png
      :width: 600 px
      :alt: Applications page

#. Check :guilabel:`Assign Floating IP` and click :guilabel:`Next` to proceed:

   .. image:: ../figures/qs_quick_deploy.png
      :width: 600 px
      :alt: Configure Application dialog 1

#. Select the :guilabel:`Instance Image` from the drop-down list and click
   :guilabel:`Create`:

   .. image:: ../figures/qs_quick_deploy_2.png
      :width: 600 px
      :alt: Configure Application dialog 2

#. Now the Apache HTTP Server application is successfully added to the newly
   created ``quick-env-4`` environment.
   Click the :guilabel:`Deploy This Environment` button
   to start the deployment:

   .. image:: ../figures/qs_quick_env.png
      :width: 600 px
      :alt: Environment "quick-env-1" page

   It may take some time for the environment to deploy. Wait until the status
   is changed from ``Deploying`` to ``Ready``.

#. Navigate to :menuselection:`Applications > Catalog > Environments` to
   view the details.


Delete an application
~~~~~~~~~~~~~~~~~~~~~

To delete an application that belongs to the environment:

#. Log in to the OpenStack dashboard.

#. Navigate to :menuselection:`Applications > Catalog > Environments`.

#. Click on the name of the environment to view its details, which include
   components, topology, and deployment history.

#. In the :guilabel:`Component List` section, click on the
   :guilabel:`Delete Component` button next to the application to be deleted.
   Confirm the deletion.

.. note::
   If an application that you are deleting has already been deployed,
   you should redeploy it to apply the recent changes. If the environment
   has not been deployed with this component, the changes are applied
   immediately on receiving the confirmation.

.. warning::
   Due to a known bug in Murano Kilo, resources allocated by a deleted
   application might not be reclaimed until the deletion of an environment.
   See `LP1417136 <https://bugs.launchpad.net/murano/+bug/1417136>`_
   for the details.