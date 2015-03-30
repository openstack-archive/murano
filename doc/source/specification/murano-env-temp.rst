..
      Copyright 2015 Telefonica I+D, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

Environment Template API
========================

Manage environment template definitions in Murano. It is possible to create, update, delete and deploy into Openstack by translating
it into an environment. In addition, applications can be added or delete to the environment template.

**Environment Template Properties**

+----------------------+------------+-------------------------------------------+
| Attribute            | Type       | Description                               |
+======================+============+===========================================+
| id                   | string     | Unique ID                                 |
+----------------------+------------+-------------------------------------------+
| name                 | string     | User-friendly name                        |
+----------------------+------------+-------------------------------------------+
| created              | datetime   | Creation date and time in ISO format      |
+----------------------+------------+-------------------------------------------+
| updated              | datetime   | Modification date and time in ISO format  |
+----------------------+------------+-------------------------------------------+
| tenant_id            | string     | OpenStack tenant ID                       |
+----------------------+------------+-------------------------------------------+
| version              | int        | Current version                           |
+----------------------+------------+-------------------------------------------+
| networking           | string     | Network settings                          |
+----------------------+------------+-------------------------------------------+
| description          | string     | The environment template specification    |
+----------------------+------------+-------------------------------------------+

**Common response codes**

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Operation completed successfully                          |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to perform the operation           |
+----------------+-----------------------------------------------------------+

Methods for Environment Template API

List Environments Templates
---------------------------

*Request*

+----------+----------------------------------+----------------------------------+
| Method   | URI                              | Description                      |
+==========+==================================+==================================+
| GET      | /templates                       | Get a list of existing           |
|          |                                  | environment templates            |
+----------+----------------------------------+----------------------------------+

*Response*

This call returns list of environment templates. Only the basic properties are
returned.

::

    {
        "templates": [
            {
                "updated": "2014-05-14T13:02:54",
                "networking": {},
                "name": "test1",
                "created": "2014-05-14T13:02:46",
                "tenant_id": "726ed856965f43cc8e565bc991fa76c3",
                "version": 0,
                "id": "2fa5ab704749444bbeafe7991b412c33"
            },
            {
                "updated": "2014-05-14T13:02:55",
                "networking": {},
                "name": "test2",
                "created": "2014-05-14T13:02:51",
                "tenant_id": "726ed856965f43cc8e565bc991fa76c3",
                "version": 0,
                "id": "744e44812da84e858946f5d817de4f72"
            }
        ]
    }


Create Environment Template
---------------------------

+----------------------+------------+---------------------------------------------------------+
| Attribute            | Type       | Description                                             |
+======================+============+=========================================================+
| name                 | string     | Environment template name; only alphanumeric characters |
|                      | and '-' |                                                         |
+----------------------+------------+---------------------------------------------------------+

*Request*

+----------+--------------------------------+--------------------------------------+
| Method   | URI                            | Description                          |
+==========+================================+======================================+
| POST     | /templates                     | Create a new environment template    |
+----------+--------------------------------+--------------------------------------+

*Content-Type*
  application/json

*Example*
   {"name": "env_temp_name"}

*Response*

::

    {
        "id": "ce373a477f211e187a55404a662f968",
        "name": "env_temp_name",
        "created": "2013-11-30T03:23:42Z",
        "updated": "2013-11-30T03:23:44Z",
        "tenant_id": "0849006f7ce94961b3aab4e46d6f229a",
    }

*Error code*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Operation completed successfully                          |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to perform the operation           |
+----------------+-----------------------------------------------------------+
| 409            | The environment template already exists                   |
+----------------+-----------------------------------------------------------+


Get Environment Templates Details
-----------------------

*Request*

Return information about environment template itself and about applications, including to this
environment template.

+----------+--------------------------------+-------------------------------------------------+
| Method   | URI                            | Description                                     |
+==========+================================+=================================================+
| GET      | /templates/{env-temp-id}       | Obtains the enviroment template information     |
+----------+--------------------------------+-------------------------------------------------+

* `env-temp-id` - environment template ID, required

*Response*

*Content-Type*
  application/json

::

     {
       "updated": "2015-01-26T09:12:51",
       "networking":
       {
       },
       "name": "template_name",
       "created": "2015-01-26T09:12:51",
       "tenant_id": "00000000000000000000000000000001",
       "version": 0,
       "id": "aa9033ca7ce245fca10e38e1c8c4bbf7",
    }

*Error code*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | OK. Environment Template created successfully             |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 404            | The environment template does not exit                    |
+----------------+-----------------------------------------------------------+

Delete Environment Template
---------------------------

*Request*

+----------+-----------------------------------+-----------------------------------+
| Method   | URI                               | Description                       |
+==========+===================================+===================================+
| DELETE   | /templates/<env-temp-id>          | Delete the template id            |
+----------+-----------------------------------+-----------------------------------+


*Parameters:*

* `env-temp_id` - environment template ID, required

*Error code*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | OK. Environment Template created successfully             |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 404            | The environment template does not exit                    |
+----------------+-----------------------------------------------------------+

Adding application to environment template
------------------------------------------

*Request*

+----------+------------------------------------+----------------------------------+
| Method   | URI                                | Description                      |
+==========+====================================+==================================+
| POST     | /templates/{env-temp-id}/services  | Create a new application         |
+----------+------------------------------------+----------------------------------+

*Parameters:*

* `env-temp-id` - The environment-template id, required
* payload - the service description

*Content-Type*
  application/json

*Example*

::

    {
        "instance": {
            "assignFloatingIp": "true",
            "keyname": "mykeyname",
            "image": "cloud-fedora-v3",
            "flavor": "m1.medium",
            "?": {
                "type": "io.murano.resources.LinuxMuranoInstance",
                "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
            }
        },
        "name": "orion",
        "port": "8080",
        "?": {
            "type": "io.murano.apps.apache.Tomcat",
            "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
        }
    }

*Response*

::


    {
       "instance":
       {
           "assignFloatingIp": "true",
           "keyname": "mykeyname",
           "image": "cloud-fedora-v3",
           "flavor": "m1.medium",
           "?":
           {
               "type": "io.murano.resources.LinuxMuranoInstance",
               "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
           }
       },
       "name": "orion",
       "?":
       {
           "type": "io.murano.apps.apache.Tomcat",
           "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
       },
       "port": "8080"
    }

*Error code*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | OK. Environment Template created successfully             |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 404            | The environment template does not exit                    |
+----------------+-----------------------------------------------------------+

Get applications information from an environment template
---------------------------------------------------------

*Request*

+----------+-------------------------------------+-----------------------------------+
| Method   | URI                                 | Description                       |
+==========+====================================+====================================+
| GET      | /templates/{env-temp-id}/services   | It obtains the service description|
+----------+-------------------------------------+-----------------------------------+

*Parameters:*

* `env-temp-id` - The environment template ID, required

*Content-Type*
  application/json

*Response*

::

    [
       {
           "instance":
           {
               "assignFloatingIp": "true",
               "keyname": "mykeyname",
               "image": "cloud-fedora-v3",
               "flavor": "m1.medium",
               "?":
               {
                   "type": "io.murano.resources.LinuxMuranoInstance",
                   "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
               }
           },
           "name": "tomcat",
           "?":
           {
               "type": "io.murano.apps.apache.Tomcat",
               "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
           },
           "port": "8080"
       },
       {
           "instance": "ef984a74-29a4-45c0-b1dc-2ab9f075732e",
           "password": "XXX",
           "name": "mysql",
           "?":
           {
               "type": "io.murano.apps.database.MySQL",
               "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
           }
       }
    ]

*Error code*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | OK. Environment Template created successfully             |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 404            | The environment template does not exit                    |
+----------------+-----------------------------------------------------------+

Create an environment from an environment template
--------------------------------------------------

*Request*

+----------+--------------------------------------------+--------------------------------------+
| Method   | URI                                        | Description                          |
+==========+================================+==================================================+
| POST     | /templates/{env-temp-id}/create-environment| Create an environment                |
+----------+--------------------------------------------+--------------------------------------+


*Parameters:*

* `env-temp-id` - The environment template ID, required

*Payload:*

* 'environment name': The environment name to be created.

*Content-Type*
  application/json

*Example*

::

    {
        "name": "environment_name"
    }

*Response*

::

    {
        "environment_id": "aa90fadfafca10e38e1c8c4bbf7",
        "name": "environment_name",
        "created": "2015-01-26T09:12:51",
        "tenant_id": "00000000000000000000000000000001",
        "version": 0,
        "session_id": "adf4dadfaa9033ca7ce245fca10e38e1c8c4bbf7",
    }

*Error code*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | OK. Environment template created successfully             |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 404            | The environment template does not exit                    |
+----------------+-----------------------------------------------------------+
| 409            | The environment already exists                            |
+----------------+-----------------------------------------------------------+