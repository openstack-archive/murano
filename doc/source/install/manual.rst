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

.. _installing_manually:

================================
 Installing and Running Manually
================================

Installing prerequisites
========================

First you need to install a number of packages with your OS package manager.
The list of packages depends on the OS you use.

* For Ubuntu run:

  ::

     $ sudo apt-get install python-setuptools python-dev

* For Fedora:

  ::

     $ sudo yum install gcc python-setuptools python-devel


  .. note::
     Fedora support wasn't thoroughly tested. We do not guarantee that Murano
     will work on Fedora.

* For CentOS:

  ::

     $ sudo yum install gcc python-setuptools python-devel
     $ sudo easy_install pip


Installing the API service and Engine
=====================================

1. Clone the Murano git repository to the management server:

   ::

      $ cd /opt/stack
      $ git clone https://git.openstack.org/stackforge/murano.git

2. Configure the database. Murano can run with MySQL and SQLite. MySQL is
   required for produciton installation, SQLite can be used for developemnt
   purposes only. Let's setup MySQL database for Murano:

   ::

      $ apt-get install python-mysqldb mysql-server
      $ mysql -u root -p
      mysql> CREATE DATABASE murano;
      mysql> GRANT ALL PRIVILEGES ON murano.* TO 'murano'@'localhost' \
        IDENTIFIED BY 'MURANO_DBPASS';
      mysql> exit;

3. Copy the sample configuration from the source tree to their final location:

   ::

      $ mkdir -p /etc/murano
      $ cp etc/murano/murano.conf.sample /etc/murano/murano.conf
      $ cp etc/murano/murano-paste.ini /etc/murano/

4. Edit ``/etc/murano/murano.conf``

   TODO(ruhe): document configuration options

5. Create database tables for Murano:

   ::

      $ tox -e venv -- murano-db-manage --config-file /etc/murano/murano.conf upgrade

6. Launch Murano API service:

   ::

      $ tox -e venv -- murano-api --config-file /etc/murano/murano.conf

7. Launch Murano Engine service:

   ::

      $ tox -e venv -- murano-engine --config-file /etc/murano/murano.conf
