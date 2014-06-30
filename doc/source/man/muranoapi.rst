==========
murano-api
==========

-----------------------------
Murano API Server
-----------------------------

:Author: openstack@lists.openstack.org
:Date:   2013-04-04
:Copyright: OpenStack Foundation
:Version: 0.5
:Manual section: 1
:Manual group: cloud computing


SYNOPSIS
========

  murano-api [options]

DESCRIPTION
===========

murano-api is a server daemon that serves the Murano API

OPTIONS
=======

  **General options**

  **-v, --verbose**
        Print more verbose output

  **--config-file**
        Config file used for running service

  **--bind-host=HOST**
        Address of host running ``murano-api``. Defaults to `0.0.0.0`.

  **--bind-port=PORT**
        Port that ``murano-api`` listens on. Defaults to `8082`.


FILES
=====

* /etc/murano/murano.conf
* /etc/murano/murano-paste.conf

SEE ALSO
========

* `Murano <http://murano.readthedocs.org/>`__
