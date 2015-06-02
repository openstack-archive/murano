.. _use-cases:

.. toctree::
   :maxdepth: 2

=========
Use cases
=========

* *IT as a Service*

An IT organization wants to control applications, available to cloud users.
Application management should be simple and not time-consuming. Users should be
able to easily find and create the desired applications.

* *Self-service portal*

You may want to create compound combinations of applications dynamically from
simple app blocks. And you can create an environment that satisfies your
requirements in a matter of minutes. Examples of such an environment may be
“Jenkins+Java+Tomcat” or “Jenkins+Gerrit+Java+JBoss”. So testing application in
different environment combinations becomes easier.

* *Glue layer use case*

Any external service or technology may be linked to the application in the
cloud. It can be done using the powerful Murano architecture. For example,
Murano supports Docker and OracleDB applications, and to enable this support
no single change was made to Murano itself. So, users can integrate with new
external services with a minimum cost. Currently, murano applications have been
integrated with the following technologies: Docker, Legacy apps VMs or bare
metal, apps outside of OpenStack, and the following ones are planned for the
future: cloudify and TOSCA, apache brooklin, APS.
