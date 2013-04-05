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
glazier-api
==========

-----------------------------
Glazier API Server
-----------------------------

:Author: smelikyan@mirantis.com
:Date:   2013-04-04
:Copyright: Mirantis, Inc.
:Version: 2013.1-dev
:Manual section: 1
:Manual group: cloud computing


SYNOPSIS
========

  glazier-api [options]

DESCRIPTION
===========

glazier-api is a server daemon that serves the Glazier API

OPTIONS
=======

  **General options**

  **-v, --verbose**
        Print more verbose output

  **--config-file**
        Config file used for running service

  **--bind-host=HOST**
        Address of host running ``glazier-api``. Defaults to `0.0.0.0`.

  **--bind-port=PORT**
        Port that ``glazier-api`` listens on. Defaults to `8082`.


FILES
=====

* /etc/glazier/glazier-api.conf
* /etc/glazier/glazier-api-paste.conf

SEE ALSO
========

* `Glazier <http://glazier.mirantis.com>`__
