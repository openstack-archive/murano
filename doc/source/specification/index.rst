..
      Copyright 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

===========================
Murano API v1 specification
===========================

General information
===================

* **Introduction**

    Murano Service API is a programmatic interface used for interaction with
    Murano. Other interaction mechanisms like Murano Dashboard or Murano CLI
    should use API as underlying protocol for interaction.

* **Allowed HTTPs requests**

  * *POST*   :   To create a resource
  * *GET*    :   Get a resource or list of resources
  * *DELETE* :   To delete resource
  * *PATCH*  :   To update a resource

* **Description Of Usual Server Responses**

  * 200 ``OK`` - the request was successful.
  * 201 ``Created`` - the request was successful and a resource was created.
  * 204 ``No Content`` - the request was successful but there is no representation to return (i.e. the response is empty).
  * 400 ``Bad Request`` - the request could not be understood or required parameters were missing.
  * 401 ``Unauthorized`` - authentication failed or user didn't have permissions for requested operation.
  * 403 ``Forbidden`` - access denied.
  * 404 ``Not Found`` - resource was not found
  * 405 ``Method Not Allowed`` - requested method is not supported for resource.
  * 409 ``Conflict`` - requested method resulted in a conflict with the current state of the resource.

* **Response of POSTs and PUTs**

    All POST and PUT requests by convention should return the created object
    (in the case of POST, with a generated ID) as if it was requested by
    GET.

* **Authentication**

    All requests include a Keystone authentication token header
    (X-Auth-Token). Clients must authenticate with Keystone before
    interacting with the Murano service.

.. include:: murano-api.rst
.. include:: murano-repository.rst
.. include:: murano-env-temp.rst

