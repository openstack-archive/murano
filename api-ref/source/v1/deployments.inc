.. -*- rst -*-

===========
Deployments
===========

Deployments track environments that have been deployed, either successfully
or otherwise. Each deployment contains the following information:

* A "Class: Environment" object (io.murano.Environment) with a name. Each
  "Class: Environment" object defines an environment in terms of the deployment
  process and groups all Applications and their related infrastructures together.
* An object (or objects) referring to networks that exist.
* A list of Applications (e.g. io.murano.apps.linux.Telnet). Each Application
  contains, or otherwise references, anything it requires. The Telnet example
  has a property called ``instance`` whose contract states it must be of type
  ``io.murano.resources.Instance``. In turn, the Instance has properties it
  requires (like a ``name``, a ``flavor``, or a keypair name, ``keyname``).

List deployments
================

.. rest_method::  GET /deployments

List deployments for all environments for the current tenant (project).

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
    - deployments: deployments

Response Example
----------------

.. literalinclude:: samples/deployments-list-response.json
   :language: javascript
