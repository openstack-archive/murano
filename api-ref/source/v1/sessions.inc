.. -*- rst -*-

=============================
Environment Configuration API
=============================

Since Murano environments are available for local modification by different
users and from different locations, it's therefore necessary to store local
modifications somewhere. Thus, sessions were created to satisfy this
requirement. After a user adds applications to an environment, a new session
can be created. A session can be deployed only once.

.. note::

   Multiple sessions can be opened for one environment simultaneously, but only
   one session can be deployed at a time. Only the first session that is deployed
   will be deployed, while the other ones will become invalid, no longer
   capable of being deploying. Once an environment is in ``deploying`` or
   ``deleting`` status, a new session for the environment cannot be opened.

Configure Environment / Open Session
====================================

.. rest_method::  POST /environments/{env_id}/configure

Creates a new configuration session for environment ``env_id``.

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

   - env_id: env_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - created: created
   - updated: updated
   - environment_id: env_id
   - state: session_state
   - version: session_version
   - id: session_id

Response Example
----------------

.. literalinclude:: samples/session-create-response.json
   :language: javascript

Deploy session
==============

.. rest_method::  POST /environments/{env_id}/sessions/{session_id}/deploy

Start deployment of a murano environment session.

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

   - env_id: env_id_url
   - session_id: session_id_url

Get Session Details
===================

.. rest_method::  GET /environments/{env_id}/sessions/{session_id}

Start deployment of a murano environment session.

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

   - env_id: env_id_url
   - session_id: session_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - id: session_id
   - environment_id: env_id
   - created: created
   - updated: updated
   - user_id: session_user_id
   - version: session_version
   - state: session_state

Response Example
----------------

.. literalinclude:: samples/session-show-response.json
   :language: javascript

Delete Session
==============

.. rest_method::  DELETE /environments/{env_id}/sessions/{session_id}

Delete the session ``session_id``.

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

   - env_id: env_id_url
   - session_id: session_id_url
