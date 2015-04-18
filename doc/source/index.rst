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

==================
Welcome to Murano!
==================

Introduction
============

Murano Project introduces an application catalog, which allows application
developers and cloud administrators to publish various cloud-ready applications
in a browsable categorised catalog. It may be used by the cloud users
(including the unexperienced ones) to pick-up the needed applications and
services and composes the reliable environments out of them in a
"push-the-button" manner.

Key goal is to provide UI and API which allows to compose and deploy composite
environments on the Application abstraction level and then manage their
lifecycle.

Murano consists of several source code repositories:
    * `murano`_ - is the main repository. It contains code for Murano API
      server, Murano engine and MuranoPL
    * `murano-agent`_ - agent which runs on guest VMs and executes deployment
      plan
    * `murano-dashboard`_ - Murano UI implemented as a plugin for OpenStack
      Dashboard
    * `python-muranoclient`_ - Client library and CLI client for Murano


.. _murano: https://git.openstack.org/cgit/openstack/murano/
.. _murano-agent: https://git.openstack.org/cgit/openstack/murano-agent/
.. _murano-dashboard: https://git.openstack.org/cgit/openstack/murano-dashboard/
.. _python-muranoclient: https://git.openstack.org/cgit/openstack/python-muranoclient/


This documentation offers information on how Murano works and how to
contribute to the project.


**Installation**

.. toctree::
   :maxdepth: 1

   install/index

**Background Concepts for Murano**

.. toctree::
   :maxdepth: 1

   murano_pl/murano_pl_index
   articles/dynamic_ui
   articles/workflow
   articles/policy_enf_index


**Tutorials**

.. toctree::
   :maxdepth: 1

   articles/app_pkg
   articles/heat_support
   image_builders/index
   articles/test_docs

**Client**

.. toctree::
   :maxdepth: 1

   articles/client

**Repository**

.. toctree::
   :maxdepth: 1

   articles/repository

**Guidelines**

.. toctree::
   :maxdepth: 2

   contributing
   guidelines
   articles/debug_tips
   articles/app_migrating


**API specification**

.. toctree::
   :maxdepth: 1

   specification/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
