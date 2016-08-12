..
      Copyright 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

===============================
Welcome to Murano Documentation
===============================

**Murano** is an open source OpenStack project that
combines an application catalog with versatile
tooling to simplify and accelerate packaging and
deployment. It can be used with almost any application
and service in OpenStack.

Murano project consists of several source code repositories:

* `murano`_ - is the main repository. It contains code for Murano API server,
  Murano engine and MuranoPL.
* `murano-agent`_ - agent which runs on guest VMs and executes deployment
  plan.
* `murano-dashboard`_ - Murano UI implemented as a plugin for OpenStack
  Dashboard.
* `python-muranoclient`_ - Client library and CLI client for Murano.

This documentation guides application developers
through the process of composing an application
package to get it ready for uploading to Murano.

Besides the deployment rules and requirements,
it contains information on how to manage images,
categories, and repositories using the murano client that
will surely be helpful for cloud administrators.

It also explains to end users how they can use the catalog
directly from the dashboard. These include guidance on how
to manage applications and environments.

And it provides information on how to contribute to the project.

.. note::
   `Deploying Murano` and `Contributing` guides are under development
   at the moment. The most recently updated information is published
   as the :ref:`BETA version of the Murano documentation <content>`.


.. Links

.. _murano: https://git.openstack.org/cgit/openstack/murano/
.. _murano-agent: https://git.openstack.org/cgit/openstack/murano-agent/
.. _murano-dashboard: https://git.openstack.org/cgit/openstack/murano-dashboard/
.. _python-muranoclient: https://git.openstack.org/cgit/openstack/python-muranoclient/


Introduction to Murano
~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   intro/key_features
   intro/target_users
   intro/architecture
   intro/use_cases


Using Murano
~~~~~~~~~~~~

This guide provides murano end users with information on how they can use the
Application Catalog directly from the Dashboard and through the command-line
interface (CLI). The screenshots provided in this guide are of the Liberty
release.

.. toctree::
   :maxdepth: 2

   enduser-guide/quickstart
   enduser-guide/manage_environments
   enduser-guide/manage_applications
   enduser-guide/log_in_to_murano_instance
   enduser-guide/use_cli
   enduser-guide/deploying_using_cli
   articles/multi_region


Developing Applications
~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   appdev-guide/step_by_step
   appdev-guide/exec_plan
   appdev-guide/hot_packages
   appdev-guide/murano_pl
   appdev-guide/murano_packages
   appdev-guide/murano_bundles
   appdev-guide/app_migrating
   appdev-guide/app_unit_tests
   appdev-guide/cinder_volume_supporting
   appdev-guide/examples
   appdev-guide/use_cases
   appdev-guide/app_debugging
   appdev-guide/faq


Miscellaneous
~~~~~~~~~~~~~

**Background Concepts for Murano**

.. toctree::
   :maxdepth: 1

   articles/workflow


**Tutorials**

.. toctree::
   :maxdepth: 1

   image_builders/index
   articles/test_docs


**Guidelines**

.. toctree::
   :maxdepth: 2

   contributing
   guidelines
   articles/debug_tips

**Gerrit review dashboard**

.. toctree::
   :maxdepth: 1

   murano_gerrit_dashboard


**API specification**

.. toctree::
   :maxdepth: 1

   specification/index


Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

