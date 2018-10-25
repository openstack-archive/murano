===============================
Welcome to Murano Documentation
===============================

**Murano** is an open source OpenStack project that combines an application
catalog with versatile tooling to simplify and accelerate packaging and
deployment. It can be used with almost any application and service in
OpenStack.

Murano project consists of several source code repositories:

* `murano`_ -- the main repository. It contains code for Murano API server,
  Murano engine and MuranoPL.
* `murano-agent`_ -- the agent that runs on guest VMs and executes the
  deployment plan.
* `murano-dashboard`_ -- Murano UI implemented as a plugin for the OpenStack
  Dashboard.
* `python-muranoclient`_ -- Client library and CLI client for Murano.

.. note::
   `Administrator Documentation`, `Contributor Documentation`, and `Appendix`
   are under development at the moment.

.. Links

.. _murano: https://git.openstack.org/cgit/openstack/murano/
.. _murano-agent: https://git.openstack.org/cgit/openstack/murano-agent/
.. _murano-dashboard: https://git.openstack.org/cgit/openstack/murano-dashboard/
.. _python-muranoclient: https://git.openstack.org/cgit/openstack/python-muranoclient/


Introduction to Murano
~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   reference/overview_index


Using Murano
~~~~~~~~~~~~

Learn how to use the Application Catalog directly from the Dashboard and
through the command-line interface (CLI), manage applications and environments.
The screenshots provided in this guide are of the Liberty release.

.. toctree::
   :maxdepth: 1

   user/quickstart/quickstart
   user/user_index

Installation
~~~~~~~~~~~~

.. toctree::
  :maxdepth: 2

  install/index

Configuration
~~~~~~~~~~~~~

.. toctree::
  :maxdepth: 2

  configuration/index

CLI Guide
~~~~~~~~~

.. toctree::
  :maxdepth: 2

  cli/index

Administrator Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Learn how to manage images, categories, and repositories using the Murano
client.

.. toctree::
   :maxdepth: 1

   admin/index

First App Guide
~~~~~~~~~~~~~~~

A guide for developing your first Murano application.

.. toctree::
   :maxdepth: 1

   first-app/index

Application Developer Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Learn how to compose an application package and get it ready for uploading to
Murano.

.. toctree::
   :maxdepth: 1

   admin/appdev-guide/developer_index
   admin/appdev-guide/faq

Contributor Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~

Learn how to contribute to the project.

.. toctree::
   :maxdepth: 1

   contributor/contributor_index

Other Documentation
~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   reference/appendix/appendix_index
   reference/appendix/articles/articles_index
