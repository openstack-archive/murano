.. _architecture:

============
Architecture
============

Murano is composed of the following major components:

* murano command-line client
* murano-dashboard
* murano-api
* murano-engine
* murano-agent

They interact with each other as illustrated in the following diagram:

.. image:: architecture.png
   :width: 600 px
   :alt: Murano architecture

All remote operations on users' servers, such as software installation
and configuration, are carried out through an AMQP queue to the murano-agent.
Such communication can easily be configured on a separate instance of AMQP
to ensure that the infrastructure and servers are isolated.

Besides, Murano uses other OpenStack services to prevent the reimplementation
of the existing functionality. Murano interacts with these services using
their REST API through their python clients.

The external services used by Murano are:

* the **Orchestration service** (Heat) to orchestrate infrastructural
  resources such as servers, volumes, and networks. Murano dynamically
  creates heat templates based on application definitions.

* the **Identity service** (Keystone) to make murano API available
  to all OpenStack users.