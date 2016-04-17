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

   draft/intro/key_features
   draft/intro/target_users
   draft/intro/architecture
   draft/intro/use_cases


Using Murano
~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   draft/enduser-guide/quickstart
   draft/enduser-guide/manage_environments
   draft/enduser-guide/manage_applications
   draft/enduser-guide/log_in_to_murano_instance
   draft/enduser-guide/use_cli
   draft/enduser-guide/deploying_using_cli


Developing Applications
~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   draft/appdev-guide/step_by_step
   draft/appdev-guide/exec_plan
   draft/appdev-guide/hot_packages
   draft/appdev-guide/murano_pl
   draft/appdev-guide/murano_packages
   draft/appdev-guide/app_migrating
   draft/appdev-guide/app_unit_tests
   draft/appdev-guide/examples
   draft/appdev-guide/use_cases
   draft/appdev-guide/faq


Miscellaneous
~~~~~~~~~~~~~

**Installation**

.. toctree::
   :maxdepth: 1

   install/index

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


**API specification**

.. toctree::
   :maxdepth: 1

   specification/index


Indices and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

