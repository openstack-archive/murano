.. -*- rst -*-

============
Environments
============

List environments
=================

.. rest_method::  GET /environments

Get a list of existing Environments

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 500

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - all_tenants: all_tenants

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - environments: environments
   - status: env_status
   - updated: updated
   - networking: networking
   - name: env_name
   - created: created
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

Creates a environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 400
   - 401
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
   - created: created
   - updated: updated
   - tenant_id: tenant_id
   - version: env_version

Response Example
----------------

.. literalinclude:: samples/environment-create-response.json
   :language: javascript

Update environment
==================

.. rest_method::  PUT /environments/<env_id>

Updates an environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 202

.. rest_status_code:: error status.yaml

   - 400
   - 403
   - 404
   - 409
   - 500

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

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
   - created: created
   - updated: updated
   - tenant_id: tenant_id
   - version: env_version

Response Example
----------------

.. literalinclude:: samples/environment-update-response.json
   :language: javascript

Show environment details
========================

.. rest_method::  GET /environments/{id}

Shows details for a environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 404
   - 500

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - id: env_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - status: env_status
   - updated: updated
   - networking: networking
   - name: env_name
   - created: created
   - tenant_id: tenant_id
   - version: env_version
   - services: services
   - id: env_id

Response Example
----------------

.. literalinclude:: samples/environment-show-response.json
   :language: javascript

Delete environment
==================

.. rest_method::  DELETE /environments/{id}

Remove specified Environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 403
   - 404
   - 500

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - id: env_id_url
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

   - 400
   - 401
   - 500

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
   - name: env_name
   - regions: regions
   - services: services
   - ?: env_model

Response Example
----------------

.. literalinclude:: samples/environments-model-response.json
   :language: javascript

Update environment model
========================

.. rest_method::  PATCH /environments/<env_id>/model/

Update an Environment model.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 202

.. rest_status_code:: error status.yaml

   - 400
   - 403
   - 404
   - 409
   - 500

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - name: env_name_update

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
   - name: env_name
   - regions: regions
   - services: services
   - ?: env_model

Response Example
----------------

.. literalinclude:: samples/environments-model-response.json
   :language: javascript

Get environment last status
===========================

.. rest_method::  GET /environments/{id}/lastStatus

Get last status for a environment.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 404
   - 500

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - id: env_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - uuid: last_status_uuid

Response Example
----------------

.. literalinclude:: samples/environment-last-status-response.json
   :language: javascript
