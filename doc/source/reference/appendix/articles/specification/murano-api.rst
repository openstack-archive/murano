Glossary
========

.. _glossary-environment:

* **Environment**

    The environment is a set of applications managed by a single project (tenant). They could be related logically with each other or not.
    Applications within a single environment may comprise of complex configuration while applications in different environments are always
    independent from one another. Each environment is associated with a single OpenStack project.

.. _glossary-sessions:

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

* `tenant` - indicates environments from specified tenant are listed. Admin user required.

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

Multiple :ref:`sessions <glossary-sessions>` could be opened for one environment
simultaneously, but only one session going to be deployed. First session that
starts deploying is going to be deployed; other ones become invalid and could
not be deployed at all.
User could not open new session for environment that in
*deploying* state (that's why we call it "almost lock free" model).

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

During this call a new working session is created with its ID returned in response body.
Notice that the session ID should be added to request headers with name ``X-Configuration-Session``
in subsequent requests when necessary.

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
      "id": "257bef44a9d848daa5b2563779714820",
      "updated": datetime.datetime(2014, 5, 14, 14, 17, 58, 949358),
      "environment_id": "744e44812da84e858946f5d817de4f72",
      "ser_id": "4e91d06270c54290b9dbdf859356d3b3",
      "created": datetime.datetime(2014, 5, 14, 14, 17, 58, 949305),
      "state": "open",
      "version": 0L
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
| 404            | Not found. Specified environment doesn`t exist            |
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
| 404            | Not found. Specified session or environment doesn`t exist |
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
| 404            | Not found. Specified session or environment doesn`t exist |
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
| 404            | Not found. Specified session or environment doesn`t exist |
+----------------+-----------------------------------------------------------+

Environment model API
=====================

Get environment model
---------------------

+----------+-------------------------------------+------------------------+--------------------------+
| Method   | URI                                 | Header                 | Description              |
+==========+=====================================+========================+==========================+
| GET      | /environments/<env_id>/model/<path> | X-Configuration-Session| Get an Environment model |
|          |                                     | (optional)             |                          |
+----------+-------------------------------------+------------------------+--------------------------+

Specifying <path> allows to get a specific section of the model, for example
`defaultNetworks`, `region` or `?` or any of the subsections.

*Response*

**Content-Type**
  application/json

.. code-block:: javascript

    {
        "defaultNetworks": {
            "environment": {
                "internalNetworkName": "net_two",
                "?": {
                    "type": "io.murano.resources.ExistingNeutronNetwork",
                    "id": "594e94fcfe4c48ef8f9b55edb3b9f177"
                }
            },
            "flat": null
        },
        "region": "RegionTwo",
        "name": "new_env",
        "regions": {
            "": {
                "defaultNetworks": {
                    "environment": {
                        "autoUplink": true,
                        "name": "new_env-network",
                        "externalRouterId": null,
                        "dnsNameservers": [],
                        "autogenerateSubnet": true,
                        "subnetCidr": null,
                        "openstackId": null,
                        "?": {
                            "dependencies": {
                                "onDestruction": [{
                                    "subscriber": "c80e33dd67a44f489b2f04818b72f404",
                                    "handler": null
                                }]
                            },
                            "type": "io.murano.resources.NeutronNetwork/0.0.0@io.murano",
                            "id": "e145b50623c04a68956e3e656a0568d3",
                            "name": null
                        },
                        "regionName": "RegionOne"
                    },
                    "flat": null
                },
                "name": "RegionOne",
                "?": {
                    "type": "io.murano.CloudRegion/0.0.0@io.murano",
                    "id": "c80e33dd67a44f489b2f04818b72f404",
                    "name": null
                }
            },
            "RegionOne": "c80e33dd67a44f489b2f04818b72f404",
            "RegionTwo": {
                "defaultNetworks": {
                    "environment": {
                        "autoUplink": true,
                        "name": "new_env-network",
                        "externalRouterId": "e449bdd5-228c-4747-a925-18cda80fbd6b",
                        "dnsNameservers": ["8.8.8.8"],
                        "autogenerateSubnet": true,
                        "subnetCidr": "10.0.198.0/24",
                        "openstackId": "00a695c1-60ff-42ec-acb9-b916165413da",
                        "?": {
                            "dependencies": {
                                "onDestruction": [{
                                    "subscriber": "f8cb28d147914850978edb35eca156e1",
                                    "handler": null
                                }]
                            },
                            "type": "io.murano.resources.NeutronNetwork/0.0.0@io.murano",
                            "id": "72d2c13c600247c98e09e2e3c1cd9d70",
                            "name": null
                        },
                        "regionName": "RegionTwo"
                    },
                    "flat": null
                },
                "name": "RegionTwo",
                "?": {
                    "type": "io.murano.CloudRegion/0.0.0@io.murano",
                    "id": "f8cb28d147914850978edb35eca156e1",
                    "name": null
                }
            }
        },
        services: []
        "?": {
            "type": "io.murano.Environment/0.0.0@io.murano",
            "_actions": {
                "f7f22c174070455c9cafc59391402bdc_deploy": {
                    "enabled": true,
                    "name": "deploy",
                    "title": "deploy"
                }
            },
            "id": "f7f22c174070455c9cafc59391402bdc",
            "name": null
        }
    }

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Environment model received successfully                   |
+----------------+-----------------------------------------------------------+
| 403            | User is not authorized to access environment              |
+----------------+-----------------------------------------------------------+
| 404            | Environment is not found or specified section of the      |
|                | model does not exist                                      |
+----------------+-----------------------------------------------------------+

Update environment model
------------------------

*Request*

+----------+--------------------------------+------------------------+-----------------------------+
| Method   | URI                            | Header                 | Description                 |
+==========+================================+========================+=============================+
| PATCH    | /environments/<env_id>/model/  | X-Configuration-Session| Update an Environment model |
+----------+--------------------------------+------------------------+-----------------------------+

* **Content-Type**
  application/env-model-json-patch

  Allowed operations for paths:

  * "" (model root): no operations
  * "defaultNetworks": "replace"
  * "defaultNetworks/environment": "replace"
  * "defaultNetworks/environment/?/id": no operations
  * "defaultNetworks/flat": "replace"
  * "name": "replace"
  * "region": "replace"
  * "?/type": "replace"
  * "?/id": no operations

  For other paths any operation (add, replace or remove) is allowed.

* **Example of request body with JSON-patch**

.. code-block:: javascript

   [{
     "op": "replace",
     "path": "/defaultNetworks/flat",
     "value": true
   }]

*Response*

**Content-Type**
  application/json

See *GET* request response.

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Environment is edited successfully                        |
+----------------+-----------------------------------------------------------+
| 400            | Body format is invalid                                    |
+----------------+-----------------------------------------------------------+
| 403            | User is not authorized to access environment or specified |
|                | operation is forbidden for the given property             |
+----------------+-----------------------------------------------------------+
| 404            | Environment is not found or specified section of the      |
|                | model does not exist                                      |
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
| GET      | /deployments                       | Get list of deployments for all      |
|          |                                    | environments in user's project       |
+----------+---------------------------------------------------------------------------+

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

Create new application
----------------------

Create a new application and add it to the murano environment.
Result JSON is calculated in Murano dashboard, which is based on `UI definition <https://git.openstack.org/cgit/openstack/murano/tree/doc/source/appdev-guide/muranopackages/dynamic_ui.rst>`_.

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
| 200            | Application was created successfully                      |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized to perform this action             |
+----------------+-----------------------------------------------------------+
| 403            | Policy prevents this user from performing this action     |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Environment doesn't exist                      |
+----------------+-----------------------------------------------------------+
| 400            | Required header or body are not provided                  |
+----------------+-----------------------------------------------------------+

Update applications
-------------------

Applications list for environment can be updated.

*Request*

**Content-Type**
  application/json

+----------------+-----------------------------------------------------------+------------------------------------+
| Method         | URI                                                       | Header                             |
+================+===========================================================+====================================+
| PUT            | /environments/<env_id>/services                           | X-Configuration-Session            |
+----------------+-----------------------------------------------------------+------------------------------------+

::

    [{
        "instance": {
            "availabilityZone": "nova",
            "name": "apache-instance",
            "assignFloatingIp": true,
            "keyname": "",
            "flavor": "m1.small",
            "image": "146d5523-7b2d-4abc-b0d0-2041f920ce26",
            "?": {
                "type": "io.murano.resources.LinuxMuranoInstance",
                "id": "25185cb6f29b415fa2e438309827a797"
            }
        },
        "name": "ApacheHttpServer",
        "enablePHP": true,
        "?": {
            "type": "com.example.apache.ApacheHttpServer",
            "id": "6e66106d7dcb4748a5c570150a3df80f"
        }
    }]


*Response*

Updated applications list returned


**Content-Type**
  application/json

::

    [{
        "instance": {
            "availabilityZone": "nova",
            "name": "apache-instance",
            "assignFloatingIp": true,
            "keyname": "",
            "flavor": "m1.small",
            "image": "146d5523-7b2d-4abc-b0d0-2041f920ce26",
            "?": {
                "type": "io.murano.resources.LinuxMuranoInstance",
                "id": "25185cb6f29b415fa2e438309827a797"
            }
        },
        "name": "ApacheHttpServer",
        "enablePHP": true,
        "?": {
            "type": "com.example.apache.ApacheHttpServer",
            "id": "6e66106d7dcb4748a5c570150a3df80f"
        }
    }]

+----------------+-----------------------------------------------------------+
| Code           | Description                                               |
+================+===========================================================+
| 200            | Services are updated successfully                         |
+----------------+-----------------------------------------------------------+
| 400            | Required header is not provided                           |
+----------------+-----------------------------------------------------------+
| 401            | User is not authorized                                    |
+----------------+-----------------------------------------------------------+
| 403            | Session is in deploying state and could not be updated    |
|                | or user is not allowed to update services                 |
+----------------+-----------------------------------------------------------+
| 404            | Not found. Specified environment and/or session do not    |
|                | exist                                                     |
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
