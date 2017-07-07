.. _step-by-step:

Developing Murano Packages 101
==============================

Murano provides a very powerful and flexible platform to automate the
provisioning, deployment, configuration and lifecycle management of
applications in OpenStack clouds. However, the flexibility comes at cost: to
manage an application with Murano one has to design and develop special
scenarios which will tell Murano how to handle different aspects of application
lifecycle. These scenarios are usually called "Murano Applications" or "Murano
Packages". It is not hard to build them, but it requires some time to get
familiar with Murano's DSL to define these scenarios and to learn the common
patterns and best practices. This article provides a basic introductory course
of these aspects and aims to be the starting point for the developers willing
to learn  how to develop Murano Application packages with ease.

The course consists of the following parts:

.. toctree::
   :maxdepth: 2

   part1
   part2
   part3
   part4

.. #. Creating your first Application Package
.. #. Adding User Interface to your package and other improvements
.. #. Modifying the application to do something useful
.. #. Adding scalability scenarios
.. #. Learning some advanced stuff for production-grade deployments

Before you proceed, please ensure that you have an OpenStack cloud
(devstack-based will work just fine) and the latest version of Murano deployed.
This guide assumes that the reader has a basic knowledge of some programming
languages and object-oriented design and is a bit familiar with the scripting
languages used to configure Linux servers. Also it would be beneficial to be
familiar with YAML format: lots of software configuration tools nowadays use
YAML, and Murano is no different.

