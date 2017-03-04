====================================
Application Catalog service overview
====================================
The Application Catalog service consists of the following components:

``murano`` command-line client
  A CLI that communicates with the ``murano-api`` to publish various
  cloud-ready applications on new virtual machines.

``murano-api`` service
  An OpenStack-native REST API that processes API requests by sending
  them to the ``murano-engine`` service via AMQP.

``murano-agent`` service
  The agent that runs on guest VMs and executes the deployment plan,
  a combination of execution plan templates and scripts.

``murano-engine`` service
  The workflow component of Murano, responsible for the deployment of an
  environment.

``murano-dashboard`` service
  Murano UI implemented as a plugin for the OpenStack Dashboard.
