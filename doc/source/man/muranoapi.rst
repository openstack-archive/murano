..
      Copyright (c) 2013 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

           http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

==========
murano-api
==========

-----------------------------
Murano API Server
-----------------------------

:Author: smelikyan@mirantis.com
:Date:   2013-04-04
:Copyright: Mirantis, Inc.
:Version: 2013.1-dev
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

* /etc/murano-api/murano-api.conf
* /etc/murano-api/murano-api-paste.conf

SEE ALSO
========

* `Murano <http://murano.mirantis.com>`__
