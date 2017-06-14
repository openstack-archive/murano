.. -*- rst -*-

==========================
Actions and Static Actions
==========================

A Murano action is a type of MuranoPL method. The differences between a regular
MuranoPL method are:

* Action is executed on deployed objects.
* Action execution is initiated by API request: you do not have to call the
  method manually.

Thus, Murano actions allow performing any operations on objects, like:

* Getting information from the VM, like a config that is generated during the
  deployment
* VM rebooting
* Scaling

A list of available actions is formed during the environment deployment.
Following deployment completion, you can call the action asynchronously. Murano
engine generates a task for every action thereby allowing the action status to
be tracked.

Execute action
==============

.. rest_method::  POST /environments/{environment_id}/actions/{action_id}

Execute action on deployed environment.

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - environment_id: env_id_url
   - action_id: action_id_url

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403
   - 404

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - task_id: task_id

Response Example
----------------

.. literalinclude:: samples/execute-action-response.json
   :language: javascript

Get Action Result
=================

.. rest_method::  GET /environments/{environment_id}/actions/{task_id}

Retrieve action result for action executed on deployed environment.

Request Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - environment_id: env_id_url
   - task_id: task_id_url

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403
   - 404

Execute static action
=====================

.. rest_method::  POST /actions

Execute static action.

Static methods can be called if they are exposed by specifying Scope: Public
in the MuranoPL object and the result of its execution will be returned.

Request Example
---------------

.. literalinclude:: samples/static-action-request.json
   :language: javascript

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403
   - 404

Response Example
----------------

.. literalinclude:: samples/static-action-response.json
   :language: javascript
