.. _key-features:

============
Key features
============

Murano has a number of features designed to
interact with the application catalog, for instance
managing  what's in the catalog, and determining
how apps in the catalog are deployed.

Application catalog
~~~~~~~~~~~~~~~~~~~

#. Easy browsing:

   * Icons display applications for point-and-click
     and drag-and-drop selection and deployment.

   * Each application provides configuration information
     required for deploying it to a cloud.

   * An application topology of your environment is available
     in a separate tab, and shows the number of instances
     spawned by each application.

   * The presence of the :guilabel:`Quick Deploy` button
     on the applications page saves the time.

#. Quick filtering by:

   * Tags and words included in application name and description.
   * Recent activity.
   * Predefined category.

#. Dependency tracking:

   * Automatic detection of dependent applications that minimizes
     the possibility of an application deployment with incorrect
     configuration.

   * No underlying IaaS configuration knowledge is required.


Application catalog management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Easy application uploading using UI or CLI from:

   * Local zip file.
   * URL.
   * Package name, using an application repository.

#. Managing applications include:

   * Application organization in categories or transfer between them.
   * Application name, description and tags update.
   * Predefined application categories list setting.

#. Deployment tracking includes the availability of:

   * Logs for deployments via UI.
   * Deployment modification history to track the recent changes.


Application lifecycle management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Simplified configuration and integration:

   * It is up to an application developer to decide what their application
     will be able to do.

   * Dependencies between applications are easily configured.

   * New applications can be connected with already existing ones.

   * Well specified application actions are available.

#. HA-mode and auto-scaling:

   * Application authors can set up any available monitoring system to track
     application events and call corresponding actions, such as
     failover, starting additional instances, and others.

#. Isolation:

   * Applications in the same environments can easily interact with
     each other, though applications between different projects (tenants) are isolated.




