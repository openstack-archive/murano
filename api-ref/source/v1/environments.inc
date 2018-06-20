.. -*- rst -*-

============
Environments
============

An environment is a set of logically connected applications that are grouped
together for easy management. By default, each environment has a single
network for all its applications, and the deployment of the environment is
defined in a single heat stack. Applications in different environments are
always independent from one another.

An environment is a single unit of deployment. This means that you can not only
deploy an environment that contains a single application but an environment
that contains multiple applications.

List environments
=================

.. rest_method::  GET /environments

Get a list of existing Environments

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - all_tenants: all_tenants
   - tenant: tenant

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - environments: environments
   - status: env_status
   - created: created
   - updated: updated
   - name: env_name
   - description_text: env_description
   - tenant_id: tenant_id
   - version: env_version
   - id: env_id

Response Example
----------------

.. literalinclude:: samples/environments-list-response.json
   :language: javascript

Create environment
==================

.. rest_method::  POST /environments

Creates an environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 409

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - name: env_name_request

Request Example
---------------

.. literalinclude:: samples/environment-create-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - id: env_id
   - name: env_name
   - description_text: env_description
   - created: created
   - updated: updated
   - tenant_id: tenant_id
   - version: env_version
   - services: services
   - acquired_by: acquired_by

Response Example
----------------

.. literalinclude:: samples/environment-create-response.json
   :language: javascript

Rename environment
==================

.. rest_method::  PUT /environments/{env_id}

Renames an environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 409

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_id: env_id_url
   - name: env_name_update

Request Example
---------------

.. literalinclude:: samples/environment-update-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - id: env_id
   - name: env_name
   - description_text: env_description
   - created: created
   - updated: updated
   - tenant_id: tenant_id
   - version: env_version
   - services: services
   - acquired_by: acquired_by

Response Example
----------------

.. literalinclude:: samples/environment-update-response.json
   :language: javascript

Show environment details
========================

.. rest_method::  GET /environments/{env_id}

Shows details for an environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_id: env_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - id: env_id
   - name: env_name
   - description_text: env_description
   - created: created
   - updated: updated
   - tenant_id: tenant_id
   - version: env_version
   - services: services
   - acquired_by: acquired_by

Response Example
----------------

.. literalinclude:: samples/environment-show-response.json
   :language: javascript

Delete environment
==================

.. rest_method::  DELETE /environments/{env_id}

Remove specified Environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_id: env_id_url
   - abandon: abandon

Response Parameters
-------------------

This request does not return anything in the response body.

Get environment model
=====================

.. rest_method::  GET /environments/{env_id}/model/{path}

Get an Environment model.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_id: env_id_url
   - path: env_model_path

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - defaultNetworks: env_default_networks
   - region: env_region
   - regions: regions
   - name: env_name
   - services: services
   - ?: env_model

Response Example
----------------

.. literalinclude:: samples/environments-model-response.json
   :language: javascript

Update environment model
========================

.. rest_method::  PATCH /environments/{env_id}/model/

Update an environment model.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 202

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 409

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_id: env_id_url

Request Example
---------------

.. literalinclude:: samples/environment-model-update-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - defaultNetworks: env_default_networks
   - region: env_region
   - regions: regions
   - name: env_name
   - services: services
   - ?: env_model

Response Example
----------------

.. literalinclude:: samples/environments-model-response.json
   :language: javascript

Get environment last status
===========================

.. rest_method::  GET /environments/{env_id}/lastStatus

Get the last status for the environment for each service in the environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_id: env_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - lastStatuses: env_last_status

Response Example
----------------

.. literalinclude:: samples/environment-last-status-response.json
   :language: javascript
