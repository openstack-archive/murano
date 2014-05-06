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

.. _class_definitions:

==================================
Murano PL System Class Definitions
==================================

Murano program language has system classes, which make deploying process as convenient as it could be.
System classes are used in user class definitions for a custom applications. This article is going to help users to operate with Murano PL classes without any issues.
All classes are located in the murano-engine component and don`t require particular import.

- :ref:`io.murano.system.Resources`
- :ref:`io.murano.system.Agent`
- :ref:`io.murano.system.AgentListener`
- :ref:`io.murano.system.HeatStack`
- :ref:`io.murano.system.InstanceNotifier`
- :ref:`io.murano.system.NetworkExplorer`
- :ref:`io.murano.system.StatusReporter`

.. _io.murano.system.Resources:

io.murano.system.Resources
==========================
Used to provide API to all files, located in the Resource directory of application package. Those Resources usually used in an application deployment and needed to be specified in a workflow definition.
Available methods:

- *yaml* return resource file in yaml format
- *string* return resource file as string
- *json* return resource in json format

.. _io.murano.system.Agent:

io.murano.system.Agent
======================
Defines Murano Agent and ways of interacting with it.
Available methods:

- *call(template, resources)* - send an execution plan template and resource object, and wait for an operation to complete
- *send(template, resources)* - send execution plan template and resource class instance and continue execution without waiting for an end of the execution
- *callRaw(plan)* - send ready-to-perform murano agent execution plan and wait for an operation to complete
- *sendRaw(plan)* - send ready-to-perform murano agent execution plan and continue workflow execution
- *queueName()* - returns name of the queue with which Agent is working

.. _io.murano.system.AgentListener:

io.murano.system.AgentListener
==============================
Used for monitoring Murano Agent.

- *start()* - start to monitor Murano Agent activity
- *stop()* - stop to monitor Murano Agent activity
- *subscribe(message_id, event)* - subscribe to the specified Agent event
- *queueName()* - returns name of the queue with which Agent is working

.. _io.murano.system.HeatStack:

io.murano.system.HeatStack
==========================
Manage Heat stack operations.

- *current()* - returns current heat template
- *parameters()* - returns heat template parameters
- *reload()* - reload heat template
- *setTemplate(template)* - load heat template
- *updateTemplate(template)* - update current template with the specified part of heat stack
- *output()* - result of heat template execution
- *push()* - commit changes (requires after setTemplate and updateTemplate operations)
- *delete()* - delete current heat stack

.. _io.murano.system.InstanceNotifier:

io.murano.system.InstanceNotifier
=================================
Monitor application and instance statistics to provide billing feature.

- *trackApplication(instance,* ``title``, ``unitCount``) - start to monitor an application activity; title, unitCount - are optional
- *untrackApplication(instance)* - stop to monitor an application activity
- *trackCloudInstance(instance)* -  start to monitor an instance activity
- *untrackCloudInstance(instance)* - stop to monitor an instance activity

.. _io.murano.system.NetworkExplorer:

io.murano.system.NetworkExplorer
================================
Determines and configures network topology.

- *getDefaultRouter()* - determine default router
- *getAvailableCidr(routerId, netId)* - searching for non-allocated CIDR
- *getDefaultDns()* - get dns from config file
- *getExternalNetworkIdForRouter(routerId)* - Check for router connected to the external network
- *getExternalNetworkIdForNetwork(networkId)* - For each router this network is connected to check whether the router has external_gateway set

.. _io.murano.system.StatusReporter:

io.murano.system.StatusReporter
===============================
Provides feedback feature. To follow the deployment process in the UI, all status changes should be included in the application configuration.

- *report(instance, msg)* - Send message about an application deployment process
- *report_error(instance, msg)* - Report an error during an application deployment process
