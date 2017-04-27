.. -*- rst -*-

=====================
Environment Templates
=====================

An environment template specifies a set of virtual resources and application
information that can be deployed on top of OpenStack by translation this
information into an application-ready environment. Environment templates can
be customized, created, deleted and modified by users. Environment templates
can be instantied as many times as the user desires. For example, the user can
have different deployments from the same environment template: one for testing
and another for production.

The workflow for the creation and the instantiation of the environment template
is as follows:

#. Creation of the environment template (including application information)
#. Transformation of the environment template into the environment
   (creation of the environment and session and adding applications to the
   environment)
#. Deployment of the environment on top of Openstack

Each environment template consists of services, which specify the application
information. Each service includes information about the applications that
will be installed (e.g. Tomcat), including application properties like
the Tomcat port. Additional information pertaining to the virtual server
may be specified, if applicable, such as keyname, flavor, image, etc.

The following is an example of an environment template::

   {
      "name": "env_template_name",
      "services": [
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
            "name": "tomcat",
            "port": "8080",
            "?": {
               "type": "io.murano.apps.apache.Tomcat",
               "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
            }
         }
      ]
   }

List environment templates
==========================

.. rest_method::  GET /templates

Get a list of environment templates.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

    - is_public: template_is_public_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - templates: templates
   - created: created
   - updated: updated
   - name: template_name
   - tenant_id: tenant_id
   - version: template_version
   - description_text: template_description
   - is_public: template_is_public
   - id: template_id

Response Example
----------------

.. literalinclude:: samples/templates-list-response.json
   :language: javascript

Create environment template
===========================

.. rest_method::  POST /templates

Create an environment template.

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

   - name: template_name
   - is_public: template_is_public

Request Example
---------------

.. literalinclude:: samples/template-create-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - created: created
   - updated: updated
   - name: template_name
   - tenant_id: tenant_id
   - version: template_version
   - description_text: template_description
   - is_public: template_is_public
   - id: template_id

Response Example
----------------

.. literalinclude:: samples/template-create-response.json
   :language: javascript

Get environment template details
================================

.. rest_method::  GET /templates/{env_temp_id}

Get details for the environment template ``env_temp_id``.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - created: created
   - updated: updated
   - name: template_name
   - services: template_services
   - tenant_id: tenant_id
   - version: template_version
   - description_text: template_description
   - is_public: template_is_public
   - id: template_id

Response Example
----------------

.. literalinclude:: samples/template-show-response.json
   :language: javascript

Delete environment template
===========================

.. rest_method::  DELETE /templates/{env_temp_id}

Delete the environment template ``env_temp_id``.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url

Add application to environment template
=======================================

.. rest_method::  POST /templates/{env_temp_id}/services

Create a new application for environment template ``env_temp_id``.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url
   - service: template_service

Request Example
---------------

.. literalinclude:: samples/template-add-app-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - updated: updated
   - created: created
   - tenant_id: tenant_id
   - services: template_services
   - version: template_version
   - description_text: template_description
   - is_public: template_is_public
   - id: template_id
   - name: template_name

Response Example
----------------

.. literalinclude:: samples/template-add-app-response.json
   :language: javascript

Delete application from an environment template
===============================================

.. rest_method::  DELETE /templates/{env_temp_id}/services/{service_id}

Delete an application from an environment template.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url
   - service_id: service_id_url

List application details for environment template
=================================================

.. rest_method::  GET /templates/{env_temp_id}/services

List all the applications for the specified environment template
``env_temp_id``.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url

Response Parameters
-------------------

   - X-Openstack-Request-Id: request_id
   - updated: updated
   - created: created
   - tenant_id: tenant_id
   - services: template_services
   - version: template_version
   - description_text: template_description
   - is_public: template_is_public
   - id: template_id
   - name: template_name

Response Example
----------------

.. literalinclude:: samples/template-list-apps-response.json
   :language: javascript

Update application for an environment template
==============================================

.. rest_method::  PUT /templates/{env_temp_id}/services/{service_id}

Delete an application from an environment template.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url
   - service_id: service_id_url
   - service: template_service

Request Example
---------------

.. literalinclude:: samples/template-update-app-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - service: template_service

Response Example
----------------

.. literalinclude:: samples/template-update-app-response.json
   :language: javascript

Create environment from environment template
============================================

.. rest_method::  GET /templates/{env_temp_id}/create-environment

Create an environment from the environment template ``env_temp_id``.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404
   - 409

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url
   - name: env_name

Request Example
---------------

.. literalinclude:: samples/template-create-env-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - environment_id: env_id
   - name: env_name
   - created: created
   - tenant_id: tenant_id
   - version: env_version
   - session_id: session_id

Response Example
----------------

.. literalinclude:: samples/template-create-env-response.json
   :language: javascript

Clone environment template
==========================

.. rest_method::  GET /templates/{env_temp_id}/clone

Clones an environment template from one tenant into another.

.. note:

    In order to clone an environment template, the template *must* be
    public.

Response Codes
--------------

.. rest_status_code:: success status.yaml

   - 200

.. rest_status_code:: error status.yaml

   - 401
   - 404
   - 409

Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - env_temp_id: template_id_url
   - name: template_name

Request Example
---------------

.. literalinclude:: samples/template-clone-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - X-Openstack-Request-Id: request_id
   - environment_id: env_id
   - name: env_name
   - created: created
   - tenant_id: tenant_id
   - version: env_version
   - session_id: session_id

Response Example
----------------

.. literalinclude:: samples/template-clone-response.json
   :language: javascript
