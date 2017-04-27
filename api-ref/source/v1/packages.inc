.. -*- rst -*-

========
Packages
========

In Murano, each application, as well as the UI form for application data entry,
is defined by packages.

Package Structure
=================

The structure of the Murano application package is predefined. The application package root folder
should contain the following:

* ``manifest.yaml`` file is the application entry point.

    .. note::

        The filename is fixed, so do not use any custom names.

* ``Classes`` folder contains MuranoPL class definitions.

* ``Resources`` folder contaisn execution plan templates as well as the
  ``scripts`` folder with all the files required for an application
  deployment located inside it.

* ``UI`` folder contains the dynamic UI YAML definitions.

* ``logo.png`` file (optional) is an image file associated with your
  application. The logo appears in the Application Catalog within
  Murano Dasboard.

    .. note::

        There are no special limitations regarding an image filename.
        However, if it differs from the default ``logo.png``, specify it
        in an application manifest file.

* ``images.lst`` file (optional) contains a list of images required by an
  application.

.. note::

    A bundle is a collection of packages. In the Community App Catalog, you can
    find such bundles as ``container-based-apps``, ``app-servers``, and so on.
    The packages in the Application Catalog are sorted by usage.

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
   - 403

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
   - categories: package_categories
   - owner_id: owner_id

Response Example
----------------

.. literalinclude:: samples/packages-list-response.json
   :language: javascript

Upload package
==============

.. rest_method::  POST /v1/catalog/packages

Upload a package to the application catalog.

.. note::

   Though specifying categories is optional, it is recommended that you
   specify at least one. It helps to filter applications in the catalog.

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

   - categories: package_categories
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
   - categories: package_categories
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
   - 403
   - 404

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
   - categories: package_categories
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
   - categories: package_categories
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

   - 401
   - 403
   - 404

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
   - 403

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

Retrieve UI definition for an application.

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

   - id: pkg_id_url

Response Parameters
-------------------

Returns the entire UI definition for the package, if the logo has a
UI definition.

Below is an example of a very basic UI definition::

   Version: 2.2

   Forms:
     - appConfiguration:
         fields:
           - name: license
             type: string
             description: Apache License, Version 2.0
             hidden: false
             required: false

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
   - 403
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - id: pkg_id_url

Response Parameters
-------------------

Returns the binary logo data for the package, if the package has a logo.
