.. -*- rst -*-

==========
Categories
==========

In Murano, applications can belong to a category or multiple categories.
Administrative users can create and delete categories as well as list
available categories and view details for a particular category.

List categories
===============

.. rest_method::  GET /catalog/categories

Retrieve list of all available categories in the Application Catalog.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - categories: all_categories
   - id: category_id
   - name: category_name
   - updated: updated
   - created: created
   - package_count: package_count

Response Example
----------------

.. literalinclude:: samples/category-list-response.json
   :language: javascript

Show category details
=====================

.. rest_method::  GET /catalog/categories/{category_id}

Show details for a category.

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - category_id: category_id_url

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - id: category_id
   - name: category_name
   - updated: updated
   - created: created
   - packages: category_packages
   - package_count: package_count

Response Example
----------------

.. literalinclude:: samples/category-show-response.json
   :language: javascript

Create Category
===============

.. rest_method::  POST /catalog/categories

Add a new category to the Application Catalog.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 409

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - name: category_name

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - id: category_id
   - name: category_name
   - updated: updated
   - created: created
   - package_count: package_count

Response Example
----------------

.. literalinclude:: samples/category-create-response.json
   :language: javascript

Delete Category
===============

.. rest_method::  DELETE /catalog/categories/{category_id}

Remove an existing category from the Application Catalog.

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - category_id: category_id_url

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 403
   - 404
