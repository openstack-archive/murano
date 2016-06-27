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

Glossary
========

.. _environment:

* **Environment**

    The environment is a set of applications managed by a single project (tenant). They could be related logically with each other or not.
    Applications within a single environment may comprise of complex configuration while applications in different environments are always
    independent from one another. Each environment is associated with a single OpenStack project.

.. _`sessions`:

* **Session**

    Since murano environments are available for local modification for different users and from different locations, it's needed to store local modifications somewhere.
    Sessions were created to provide this opportunity. After a user adds an application to the environment - a new session is created.
    After a user sends an environment to deploy, a session with a set of applications changes status to *deploying* and all other open sessions for that environment become invalid.
    One session could be deployed only once.

* **Object Model**

    Applications are defined in MuranoPL object model, which is defined as a JSON object.
    The murano API doesn't know anything about it.

* **Package**

    A .zip archive, containing instructions for an application deployment.

* **Environment-Template**
    The environment template is the specification of a set of applications managed by a single project, which are
    related to each other. The environment template is stored in an environment template catalog, and it can be
    managed by the user (creation, deletion, updating). Finally, it can be deployed on OpenStack by translating
    into an environment.


Environment API
===============

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
| tenant_id            | string     | OpenStack project ID                      |
+----------------------+------------+-------------------------------------------+
| version              | int        | Current version                           |
+----------------------+------------+-------------------------------------------+
| networking           | string     | Network settings                          |
+----------------------+------------+-------------------------------------------+
| acquired_by          | string     | Id of a session that acquired this        |
|                      |            | environment (for example is deploying it) |
+----------------------+------------+-------------------------------------------+
| status               | string     | Deployment status: ready, pending,        |
|                      |            | deploying                                 |
+----------------------+------------+-------------------------------------------+

**Common response codes**

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Operation completed successfully                          |
+----------------+-----------------------------------------------------------+
| 403            | User is not authorized to perform the operation           |
+----------------+-----------------------------------------------------------+

List environments
-----------------

*Request*


+----------+----------------------------------+----------------------------------+
| Method   | URI                              | Description                      |
+==========+==================================+==================================+
| GET      | /environments                    | Get a list of existing           |
|          |                                  | Environments                     |
+----------+----------------------------------+----------------------------------+


*Parameters:*

* `all_tenants` - boolean, indicates whether environments from all projects are listed.
  *True* environments from all projects are listed. Admin user required.
  *False* environments only from current project are listed (default like option unspecified).


*Response*


This call returns a list of environments. Only the basic properties are
returned.

::

    {
        "environments": [
            {
                "status": "ready",
                "updated": "2014-05-14T13:02:54",
                "networking": {},
                "name": "test1",
                "created": "2014-05-14T13:02:46",
                "tenant_id": "726ed856965f43cc8e565bc991fa76c3",
                "version": 0,
                "id": "2fa5ab704749444bbeafe7991b412c33"
            },
            {
                "status": "ready",
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

Create environment
------------------

+----------------------+------------+--------------------------------------------------------+
| Attribute            | Type       | Description                                            |
+======================+============+========================================================+
| name                 | string     | Environment name; at least one non-white space symbol  |
+----------------------+------------+--------------------------------------------------------+

*Request*

+----------+----------------------------------+----------------------------------+
| Method   | URI                              | Description                      |
+==========+==================================+==================================+
| POST     | /environments                    | Create new Environment           |
+----------+----------------------------------+----------------------------------+

* **Content-Type**
  application/json

* **Example**
   {"name": "env_name"}

*Response*

::

    {
        "id": "ce373a477f211e187a55404a662f968",
        "name": "env_name",
        "created": "2013-11-30T03:23:42Z",
        "updated": "2013-11-30T03:23:44Z",
        "tenant_id": "0849006f7ce94961b3aab4e46d6f229a",
        "version": 0
    }


Update environment
------------------

+----------------------+------------+--------------------------------------------------------+
| Attribute            | Type       | Description                                            |
+======================+============+========================================================+
| name                 | string     | Environment name; at least one non-white space symbol  |
+----------------------+------------+--------------------------------------------------------+

*Request*

+----------+----------------------------------+----------------------------------+
| Method   | URI                              | Description                      |
+==========+==================================+==================================+
| PUT      | /environments/<env_id>           | Update an existing Environment   |
+----------+----------------------------------+----------------------------------+

* **Content-Type**
  application/json

* **Example**
  {"name": "env_name_changed"}

*Response*

**Content-Type**
  application/json

::

    {
        "id": "ce373a477f211e187a55404a662f968",
        "name": "env_name_changed",
        "created": "2013-11-30T03:23:42Z",
        "updated": "2013-11-30T03:45:54Z",
        "tenant_id": "0849006f7ce94961b3aab4e46d6f229a",
        "version": 0
    }

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Edited environment                                        |
+----------------+-----------------------------------------------------------+
| 400            | Environment name must contain at least one non-white space|
|                | symbol                                                    |
+----------------+-----------------------------------------------------------+
| 403            | User is not authorized to access environment              |
+----------------+-----------------------------------------------------------+
| 404            | Environment not found                                     |
+----------------+-----------------------------------------------------------+
| 409            | Environment with specified name already exists            |
+----------------+-----------------------------------------------------------+

Get environment details
-----------------------

*Request*

Return information about the environment itself and about applications, including this environment.

+----------+----------------------------------+-----------------------------------+----------------------------------+
| Method   | URI                              | Header                            | Description                      |
+==========+==================================+===================================+==================================+
| GET      | /environments/{id}               | X-Configuration-Session (optional)| Response detailed information    |
|          |                                  |                                   | about Environment including      |
|          |                                  |                                   | child entities                   |
+----------+----------------------------------+-----------------------------------+----------------------------------+

*Response*

**Content-Type**
  application/json

::

    {
        "status": "ready",
        "updated": "2014-05-14T13:12:26",
        "networking": {},
        "name": "quick-env-2",
        "created": "2014-05-14T13:09:55",
        "tenant_id": "726ed856965f43cc8e565bc991fa76c3",
        "version": 1,
        "services": [
            {
                "instance": {
                    "flavor": "m1.medium",
                    "image": "cloud-fedora-v3",
                    "name": "exgchhv6nbika2",
                    "ipAddresses": [
                        "10.0.0.200"
                    ],
                    "?": {
                        "type": "io.murano.resources.Instance",
                        "id": "14cce9d9-aaa1-4f09-84a9-c4bb859edaff"
                    }
                },
                "name": "rewt4w56",
                "?": {
                    "status": "ready",
                    "_26411a1861294160833743e45d0eaad9": {
                        "name": "Telnet"
                    },
                    "type": "io.murano.apps.linux.Telnet",
                    "id": "446373ef-03b5-4925-b095-6c56568fa518"
                }
            }
        ],
        "id": "20d4a012628e4073b48490a336a8acbf"
    }

Delete environment
------------------

*Request*


+----------+----------------------------------+----------------------------------+
| Method   | URI                              | Description                      |
+==========+==================================+==================================+
| DELETE   | /environments/{id}?abandon       | Remove specified Environment.    |
+----------+----------------------------------+----------------------------------+


*Parameters:*

* `abandon` - boolean, indicates how to delete environment. *False* is used if
  all resources used by environment must be destroyed; *True* is used when just
  database must be cleaned


*Response*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | OK. Environment deleted successfully                      |
+----------------+-----------------------------------------------------------+
| 403            | User is not allowed to delete this resource               |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Specified environment doesn`t exist            |
+----------------+-----------------------------------------------------------+


Environment configuration API
=============================

Multiple `sessions`_ could be opened for one environment simultaneously, but only one session going
to be deployed. First session that starts deploying is going to be deployed; other ones become invalid and could not be deployed at all.
User could not open new session for environment that in
*deploying* state (that’s why we call it "almost lock free" model).

+----------------------+------------+-------------------------------------------+
| Attribute            | Type       | Description                               |
+======================+============+===========================================+
| id                   | string     | Session unique ID                         |
+----------------------+------------+-------------------------------------------+
| environment\_id      | string     | Environment that going to be modified     |
|                      |            | during this session                       |
+----------------------+------------+-------------------------------------------+
| created              | datetime   | Creation date and time in ISO format      |
+----------------------+------------+-------------------------------------------+
| updated              | datetime   | Modification date and time in ISO format  |
+----------------------+------------+-------------------------------------------+
| user\_id             | string     | Session owner ID                          |
+----------------------+------------+-------------------------------------------+
| version              | int        | Environment version for which             |
|                      |            | configuration session is opened           |
+----------------------+------------+-------------------------------------------+
| state                | string     | Session state. Could be: open, deploying, |
|                      |            | deployed                                  |
+----------------------+------------+-------------------------------------------+

Configure environment / open session
------------------------------------

During this call new working session is created, and session ID should be sent in a request header with name ``X-Configuration-Session``.

*Request*


+----------+----------------------------------+----------------------------------+
| Method   | URI                              | Description                      |
+==========+==================================+==================================+
| POST     | /environments/<env_id>/configure | Creating new configuration       |
|          |                                  | session                          |
+----------+----------------------------------+----------------------------------+

*Response*

**Content-Type**
  application/json

::

  {
      "updated": datetime.datetime(2014, 5, 14, 14, 17, 58, 949358),
      "environment_id": "744e44812da84e858946f5d817de4f72",
      "ser_id": "4e91d06270c54290b9dbdf859356d3b3",
      "created": datetime.datetime(2014, 5, 14, 14, 17, 58, 949305),
      "state": "open", "version": 0L, "id": "257bef44a9d848daa5b2563779714820"
   }

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Session created successfully                              |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 403            | Could not open session for environment, environment has   |
|                | deploying status                                          |
+----------------+-----------------------------------------------------------+

Deploy session
--------------

With this request all local changes made within the environment start to deploy on OpenStack.

*Request*

+----------+---------------------------------+--------------------------------+
| Method   | URI                             | Description                    |
+==========+=================================+================================+
| POST     | /environments/<env_id>/sessions/| Deploy changes made in session |
|          | <session_id>/deploy             |  with specified session_id     |
+----------+---------------------------------+--------------------------------+

*Response*


+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Session status changes to *deploying*                     |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 403            | Session is already deployed or deployment is in progress  |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Specified session doesn`t exist                |
+----------------+-----------------------------------------------------------+

Get session details
-------------------

*Request*

+----------+---------------------------------+---------------------------+
| Method   | URI                             | Description               |
+==========+=================================+===========================+
| GET      | /environments/<env_id>/sessions/| Get details about session |
|          | <session_id>                    | with specified session_id |
+----------+---------------------------------+---------------------------+

*Response*


::

    {
        "id": "4aecdc2178b9430cbbb8db44fb7ac384",
        "environment_id": "4dc8a2e8986fa8fa5bf24dc8a2e8986fa8",
        "created": "2013-11-30T03:23:42Z",
        "updated": "2013-11-30T03:23:54Z",
        "user_id": "d7b501094caf4daab08469663a9e1a2b",
        "version": 0,
        "state": "deploying"
    }

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Session details information received                      |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 403            | Session is invalid                                        |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Specified session doesn`t exist                |
+----------------+-----------------------------------------------------------+

Delete session
--------------

*Request*

+----------+---------------------------------+----------------------------------+
| Method   | URI                             | Description                      |
+==========+=================================+==================================+
| DELETE   | /environments/<env_id>/sessions/| Delete session with specified    |
|          | <session_id>                    | session_id                       |
+----------+---------------------------------+----------------------------------+

*Response*

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Session is deleted successfully                           |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 403            | Session is in deploying state and could not be deleted    |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Specified session doesn`t exist                |
+----------------+-----------------------------------------------------------+

Environment deployments API
===========================

Environment deployment API allows to track changes of environment status, deployment events and errors.
It also allows to browse deployment history.

List Deployments
----------------

Returns information about all deployments of the specified environment.

*Request*

+----------+------------------------------------+--------------------------------------+
| Method   | URI                                | Description                          |
+==========+====================================+======================================+
| GET      | /environments/<env_id>/deployments | Get list of environment deployments  |
+----------+------------------------------------+--------------------------------------+

*Response*

**Content-Type**
  application/json

::

    {
        "deployments": [
            {
                "updated": "2014-05-15T07:24:21",
                "environment_id": "744e44812da84e858946f5d817de4f72",
                "description": {
                    "services": [
                        {
                            "instance": {
                                "flavor": "m1.medium",
                                "image": "cloud-fedora-v3",
                                "?": {
                                    "type": "io.murano.resources.Instance",
                                    "id": "ef729199-c71e-4a4c-a314-0340e279add8"
                                },
                                "name": "xkaduhv7qeg4m7"
                            },
                            "name": "teslnet1",
                            "?": {
                                "_26411a1861294160833743e45d0eaad9": {
                                    "name": "Telnet"
                                },
                                "type": "io.murano.apps.linux.Telnet",
                                "id": "6e437be2-b5bc-4263-8814-6fd57d6ddbd5"
                            }
                        }
                    ],
                    "defaultNetworks": {
                        "environment": {
                            "name": "test2-network",
                            "?": {
                                "type": "io.murano.lib.networks.neutron.NewNetwork",
                                "id": "b6a1d515434047d5b4678a803646d556"
                            }
                        },
                        "flat": null
                    },
                    "name": "test2",
                    "?": {
                        "type": "io.murano.Environment",
                        "id": "744e44812da84e858946f5d817de4f72"
                    }
                },
                "created": "2014-05-15T07:24:21",
                "started": "2014-05-15T07:24:21",
                "finished": null,
                "state": "running",
                "id": "327c81e0e34a4c93ad9b9052ef42b752"
            }
        ]
    }


+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Deployments information received successfully             |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this environment         |
+----------------+-----------------------------------------------------------+

Application management API
==========================

All applications should be created within an environment and all environment modifications are held within the session.
Local changes apply only after successful deployment of an environment session.

Get application details
-----------------------

Using GET requests to applications endpoint user works with list containing all
applications for specified environment. A user can request a whole list,
specific application, or specific attribute of a specific application using tree
traversing. To request a specific application, the user should add to endpoint part
an application id, e.g.: */environments/<env_id>/services/<application_id>*. For
selection of specific attribute on application, simply appending part with
attribute name will work. For example to request application name, user
should use next endpoint: */environments/<env_id>/services/<application_id>/name*

*Request*

+----------------+-----------------------------------------------------------+------------------------------------+
| Method         | URI                                                       | Header                             |
+================+===========================================================+====================================+
| GET            | /environments/<env_id>/services/<app_id>                  | X-Configuration-Session (optional) |
+----------------+-----------------------------------------------------------+------------------------------------+

**Parameters:**

* `env_id` - environment ID, required
* `app_id` - application ID, optional

*Response*

**Content-Type**
  application/json

::

    {
        "instance": {
            "flavor": "m1.medium",
            "image": "cloud-fedora-v3",
            "?": {
                "type": "io.murano.resources.Instance",
                "id": "060715ff-7908-4982-904b-3b2077ff55ef"
            },
            "name": "hbhmyhv6qihln3"
        },
        "name": "dfg34",
        "?": {
            "status": "pending",
            "_26411a1861294160833743e45d0eaad9": {
                "name": "Telnet"
            },
            "type": "io.murano.apps.linux.Telnet",
            "id": "6e7b8ad5-888d-4c5a-a498-076d092a7eff"
        }
    }

POST applications
-----------------

New application can be added to the murano environment using session.
Result JSON is calculated in Murano dashboard, which based on `UI definition <Dynamic UI Spec>`_

*Request*

**Content-Type**
  application/json

+----------------+-----------------------------------------------------------+------------------------------------+
| Method         | URI                                                       | Header                             |
+================+===========================================================+====================================+
| POST           | /environments/<env_id>/services                           | X-Configuration-Session            |
+----------------+-----------------------------------------------------------+------------------------------------+

::

    {
      "instance": {
        "flavor": "m1.medium",
        "image": "clod-fedora-v3",
        "?": {
          "type": "io.murano.resources.Instance",
          "id": "bce8308e-5938-408b-a27a-0d3f0a2c52eb"
        },
        "name": "nhekhv6r7mhd4"
      },
      "name": "sdf34sadf",
      "?": {
        "_26411a1861294160833743e45d0eaad9": {
          "name": "Telnet"
        },
        "type": "io.murano.apps.linux.Telnet",
        "id": "190c8705-5784-4782-83d7-0ab55a1449aa"
      }
    }


*Response*

Created application returned


**Content-Type**
  application/json

::

    {
        "instance": {
            "flavor": "m1.medium",
            "image": "cloud-fedora-v3",
            "?": {
                "type": "io.murano.resources.Instance",
                "id": "bce8308e-5938-408b-a27a-0d3f0a2c52eb"
            },
            "name": "nhekhv6r7mhd4"
        },
        "name": "sdf34sadf",
        "?": {
            "_26411a1861294160833743e45d0eaad9": {
                "name": "Telnet"
            },
            "type": "io.murano.apps.linux.Telnet",
            "id": "190c8705-5784-4782-83d7-0ab55a1449a1"
        }
    }

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Session is deleted successfully                           |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to access this session             |
+----------------+-----------------------------------------------------------+
| 403            | Session is in deploying state and could not be deleted    |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Specified session doesn`t exist                |
+----------------+-----------------------------------------------------------+
| 400            | Required header or body are not provided                  |
+----------------+-----------------------------------------------------------+

Delete application from environment
-----------------------------------

Delete one or all applications from the environment

*Request*

+----------------+-----------------------------------------------------------+-----------------------------------+
| Method         | URI                                                       | Header                            |
+================+===========================================================+===================================+
| DELETE         | /environments/<env_id>/services/<app_id>                  | X-Configuration-Session(optional) |
+----------------+-----------------------------------------------------------+-----------------------------------+

**Parameters:**

* `env_id` - environment ID, required
* `app_id` - application ID, optional

Statistic API
=============

Statistic API intends to provide billing feature

Instance environment statistics
-------------------------------

*Request*

Get information about all deployed instances in the specified environment

+----------------+--------------------------------------------------------------+
| Method         | URI                                                          |
+================+==============================================================+
| GET            | /environments/<env_id>/instance-statistics/raw/<instance_id> |
+----------------+--------------------------------------------------------------+

**Parameters:**

* `env_id` - environment ID, required
* `instance_id` - ID of the instance for which need to provide statistic information, optional

*Response*


+----------------------+------------+-----------------------------------------------------------------+
| Attribute            | Type       | Description                                                     |
+======================+============+=================================================================+
| type                 | int        | Code of the statistic object; 200 - instance, 100 - application |
+----------------------+------------+-----------------------------------------------------------------+
| type_name            | string     | Class name of the statistic object                              |
+----------------------+------------+-----------------------------------------------------------------+
| instance_id          | string     | Id of deployed instance                                         |
+----------------------+------------+-----------------------------------------------------------------+
| active               | bool       | Instance status                                                 |
+----------------------+------------+-----------------------------------------------------------------+
| type_title           | string     | User-friendly name for browsing statistic in UI                 |
+----------------------+------------+-----------------------------------------------------------------+
| duration             | int        | Seconds of instance uptime                                      |
+----------------------+------------+-----------------------------------------------------------------+

**Content-Type**
  application/json

::

    [
        {
            "type": 200,
            "type_name": "io.murano.resources.Instance",
            "instance_id": "ef729199-c71e-4a4c-a314-0340e279add8",
            "active": true,
            "type_title": null,
            "duration": 1053,
        }
    ]

*Request*

+----------------+--------------------------------------------------------------+
| Method         | URI                                                          |
+================+==============================================================+
| GET            | /environments/<env_id>/instance-statistics/aggregated        |
+----------------+--------------------------------------------------------------+

*Response*

+----------------------+------------+-----------------------------------------------------------------+
| Attribute            | Type       | Description                                                     |
+======================+============+=================================================================+
| type                 | int        | Code of the statistic object; 200 - instance, 100 - application |
+----------------------+------------+-----------------------------------------------------------------+
| duration             | int        | Amount uptime of specified type objects                         |
+----------------------+------------+-----------------------------------------------------------------+
| count                | int        | Quantity of specified type objects                              |
+----------------------+------------+-----------------------------------------------------------------+

**Content-Type**
  application/json

 ::

    [
        {
            "duration": 720,
            "count": 2,
            "type": 200
        }
    ]

General Request Statistics
--------------------------

*Request*

+----------------+---------------+
| Method         | URI           |
+================+===============+
| GET            | /stats        |
+----------------+---------------+

*Response*

+----------------------+------------+-----------------------------------------------------------------+
| Attribute            | Type       | Description                                                     |
+======================+============+=================================================================+
| requests_per_tenant  | int        | Number of incoming requests for user project                    |
+----------------------+------------+-----------------------------------------------------------------+
| errors_per_second    | int        | Class name of the statistic object                              |
+----------------------+------------+-----------------------------------------------------------------+
| errors_count         | int        | Class name of the statistic object                              |
+----------------------+------------+-----------------------------------------------------------------+
| requests_per_second  | float      | Average number of incoming request received in one second       |
+----------------------+------------+-----------------------------------------------------------------+
| requests_count       | int        | Number of all requests sent to the server                       |
+----------------------+------------+-----------------------------------------------------------------+
| cpu_percent          | bool       | Current cpu usage                                               |
+----------------------+------------+-----------------------------------------------------------------+
| cpu_count            | int        | Available cpu power is ``cpu_count * 100%``                     |
+----------------------+------------+-----------------------------------------------------------------+
| host                 | string     | Server host-name                                                |
+----------------------+------------+-----------------------------------------------------------------+
| average_response_time| float      | Average time response waiting, seconds                          |
+----------------------+------------+-----------------------------------------------------------------+

**Content-Type**
  application/json

::

    [
        {
            "updated": "2014-05-15T08:26:17",
            "requests_per_tenant": "{\"726ed856965f43cc8e565bc991fa76c3\": 313}",
            "created": "2014-04-29T13:23:59",
            "cpu_count": 2,
            "errors_per_second": 0,
            "requests_per_second": 0.0266528,
            "cpu_percent": 21.7,
            "host": "fervent-VirtualBox",
            "error_count": 0,
            "request_count": 320,
            "id": 1,
            "average_response_time": 0.55942
        }
    ]


Actions API
===========

Murano actions are simple MuranoPL methods, that can be called on deployed applications.
Application contains a list with available actions. Actions may return a result.

Execute an action
-----------------

Generate task with executing specified action. Input parameters may be provided.

*Request*

**Content-Type**
  application/json

+----------------+-----------------------------------------------------------+------------------------------------+
| Method         | URI                                                       | Header                             |
+================+===========================================================+====================================+
| POST           | /environments/<env_id>/actions/<action_id>                |                                    |
+----------------+-----------------------------------------------------------+------------------------------------+

**Parameters:**

* `env_id` - environment ID, required
* `actions_id` - action ID to execute, required

::

  "{<action_property>: value}"

  or

  "{}" in case action has no properties

*Response*

Task ID that executes specified action is returned

**Content-Type**
  application/json

::

  {
      "task_id": "620e883070ad40a3af566d465aa156ef"
  }

GET action result
-----------------

Request result value after action execution finish. Not all actions have return values.


*Request*

+----------------+-----------------------------------------------------------+------------------------------------+
| Method         | URI                                                       | Header                             |
+================+===========================================================+====================================+
| GET            | /environments/<env_id>/actions/<task_id>                  |                                    |
+----------------+-----------------------------------------------------------+------------------------------------+

**Parameters:**

* `env_id` - environment ID, required
* `task_id` - task ID, generated on desired action execution

*Response*

Json, describing action result is returned. Result type and value are provided.

**Content-Type**
  application/json

::

    {
      "isException": false,
        "result": ["item1", "item2"]
    }


Static Actions API
==================

Static actions are MuranoPL methods that can be called on a MuranoPL class
without deploying actual applications and usually return a result.

Execute a static action
-----------------------

Invoke public static method of the specified MuranoPL class.
Input parameters may be provided if method requires them.

*Request*

**Content-Type**
  application/json

+----------------+-----------------------------------------------------------+------------------------------------+
| Method         | URI                                                       | Header                             |
+================+===========================================================+====================================+
| POST           | /actions                                                  |                                    |
+----------------+-----------------------------------------------------------+------------------------------------+

::

  {
      "className": "my.class.fqn",
      "methodName": "myMethod",
      "packageName": "optional.package.fqn",
      "classVersion": "1.2.3",
      "parameters": {
          "arg1": "value1",
          "arg2": "value2"
      }
   }

+-----------------+------------+-----------------------------------------------------------------------------+
| Attribute       | Type       | Description                                                                 |
+=================+============+=============================================================================+
| className       | string     | Fully qualified name of MuranoPL class with static method                   |
+-----------------+------------+-----------------------------------------------------------------------------+
| methodName      | string     | Name of the method to invoke                                                |
+-----------------+------------+-----------------------------------------------------------------------------+
| packageName     | string     | Fully qualified name of a package with the MuranoPL class (optional)        |
+-----------------+------------+-----------------------------------------------------------------------------+
| classVersion    | string     | Class version specification, "=0" by default                                |
+-----------------+------------+-----------------------------------------------------------------------------+
| parameters      | object     | Key-value pairs of method parameter names and their values, "{}" by default |
+-----------------+------------+-----------------------------------------------------------------------------+

*Response*

JSON-serialized result of the static method execution.

HTTP codes:

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | OK. Action was executed successfully                      |
+----------------+-----------------------------------------------------------+
| 400            | Bad request. The format of the body is invalid, method    |
|                | doesn't match provided arguments, mandatory arguments are |
|                | not provided                                              |
+----------------+-----------------------------------------------------------+
| 403            | User is not allowed to execute the action                 |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Specified class, package or method doesn't     |
|                | exist or method is not exposed                            |
+----------------+-----------------------------------------------------------+
| 503            | Unhandled exception in the action                         |
+----------------+-----------------------------------------------------------+
