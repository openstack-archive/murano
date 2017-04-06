.. -*- rst -*-

========
Packages
========

List Packages
=============

.. rest_method::  GET /v1/catalog/packages

Get a list of packages

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

   - catalog: catalog
   - marker: marker
   - limit: limit
   - order_by: order_by
   - type: pkg_type_query
   - category: category
   - fqn: fqn
   - owned: owned
   - id: pkg_id_query
   - include_disabled: include_disabled
   - search: search
   - class_name: class_name
   - name: pkg_name_query

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - packages: packages
   - updated: updated
   - class_definitions: class_definitions
   - id: pkg_id
   - fully_qualified_name: fully_qualified_name
   - is_public: is_public
   - name: pkg_name
   - type: pkg_type
   - supplier: pkg_supplier
   - description: description
   - author: author
   - created: created
   - enabled: enabled
   - tags: tags
   - categories: categories
   - owner_id: owner_id

Response Example
----------------

.. literalinclude:: samples/packages-list-response.json
   :language: javascript

Upload package
==============

.. rest_method::  POST /v1/catalog/packages

Create a package.

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

   - categories: categories
   - is_public: is_public
   - file: pkg_file

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - updated: updated
   - class_definitions: class_definitions
   - id: pkg_id
   - fully_qualified_name: fully_qualified_name
   - is_public: is_public
   - name: pkg_name
   - type: pkg_type
   - supplier: pkg_supplier
   - description: description
   - author: author
   - created: created
   - enabled: enabled
   - tags: tags
   - categories: categories
   - owner_id: owner_id

Response Example
----------------

.. literalinclude:: samples/package-create-response.json
   :language: javascript

Show package details
====================

.. rest_method::  GET /v1/catalog/packages/{id}

Shows details for a package.

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

   - id: pkg_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - updated: updated
   - class_definitions: class_definitions
   - id: pkg_id
   - fully_qualified_name: fully_qualified_name
   - is_public: is_public
   - name: pkg_name
   - type: pkg_type
   - supplier: pkg_supplier
   - description: description
   - author: author
   - created: created
   - enabled: enabled
   - tags: tags
   - categories: categories
   - owner_id: owner_id

Response Example
----------------

.. literalinclude:: samples/package-show-response.json
   :language: javascript

Update package
==============

.. rest_method::  PATCH /v1/catalog/packages/{id}

Update a package.

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

   - id: pkg_id_url

Request Example
---------------

.. literalinclude:: samples/package-update-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - updated: updated
   - class_definitions: class_definitions
   - id: pkg_id
   - fully_qualified_name: fully_qualified_name
   - is_public: is_public
   - name: pkg_name
   - type: pkg_type
   - supplier: pkg_supplier
   - description: description
   - author: author
   - created: created
   - enabled: enabled
   - tags: tags
   - categories: categories
   - owner_id: owner_id

Response Example
----------------

.. literalinclude:: samples/package-update-response.json

Delete package
==============

.. rest_method::  DELETE /v1/catalog/packages/{id}

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

   - id: pkg_id_url

Response Parameters
-------------------

This request does not return anything in the response body.
   :language: javascript

Download package
================

.. rest_method::  GET /v1/catalog/packages/{id}/download

Download a package.

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

   - id: pkg_id_url

Response Parameters
-------------------

This request does not return anything in the response body.
   :language: javascript

Get UI definition
=================

.. rest_method::  GET /v1/catalog/packages/{id}/ui

Retrieve UI definition for a application.

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

   - id: pkg_id_url

Response Parameters
-------------------

This request does not return anything in the response body.
   :language: javascript

Get logo
========

.. rest_method::  GET /v1/catalog/packages/{id}/logo

Retrieve application logo.

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

   - id: pkg_id_url

Response Parameters
-------------------

This request does not return anything in the response body.
   :language: javascript
