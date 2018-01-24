.. _examples:

========
Examples
========

.. list-table::
   :header-rows: 1
   :widths: 30 70
   :stub-columns: 0
   :class: borderless

   * - Application name
     - Description

   * - | `Zabbix Agent`_
     - Zabbix Agent is a simple application. It doesn't deploy a VM by itself,
       but is installed on a specific VM that may contain any other
       applications. This VM is tracked by Zabbix and by its configuration.

       So Murano performs the Zabbix agent configuration based on the user
       input. The user chooses the way of instance tracking - HTTP or ICMP that may
       perform some modifications in the application package.

       It is worth noting that application scripts are written in Python, not
       in Bash as usual. This application does not work without Zabbix server
       application since it's a required property, determined in the
       application definition.

   * - | `Zabbix Server`_
     - Zabbix Server application interacts with Zabbix Agent by calling its
       setUpAgent method and providing information about itself: IP and hostname
       of VM on which the server is installed.

       Server installs MySQL database and requests database name, password and
       some other parameters from the user.

   * - | `Docker Crate`_
     - This is a good example on how difficult logic may be simplified with
       the inheritance that is supported by MuranoPL. Definition of this app is
       simple, but the opportunity it provides is fantastic.

       Crate is a distributed database, in the Murano Application catalog it
       looks like a regular application. It may be deployed on Google Kubernetes
       or regular Docker server. The user picks the desired option while filling in
       the form since these options are set in the UI definition. The form field
       has a list of possible options::

         ...
         type: 
         - com.mirantis.docker.kubernetes.KubernetesPod
         - com.mirantis.docker.DockerStandaloneHost

       Information about the application itself (docker image and port that is
       needed to be opened) is contained in the getContainer method. All other
       actions for the application configuration are located at the
       DockerStandaloneHost definition and its dependencies. Note that this
       application doesn't have a filename:Resources folder at all since the
       installation is made by Docker itself.



.. Links:
.. _`Zabbix Agent`: https://github.com/openstack/murano-apps/tree/master/ZabbixAgent/package
.. _`Zabbix Server`: https://github.com/openstack/murano-apps/tree/master/ZabbixServer/package
.. _`Docker Crate`: https://github.com/openstack/murano-apps/tree/master/Docker/Applications/Crate/package
