General information
===================

* **Introduction**

    The murano service API is a programmatic interface used for interaction with
    murano. Other interaction mechanisms like the murano dashboard or the murano CLI
    should use the API as an underlying protocol for interaction.

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
  * 406 ``Not Acceptable`` - the requested resource is only capable of generating content not acceptable
    according to the Accept headers sent in the request.
  * 409 ``Conflict`` - requested method resulted in a conflict with the current state of the resource.

* **Response of POSTs and PUTs**

    All POST and PUT requests by convention should return the created object
    (in the case of POST, with a generated ID) as if it was requested by
    GET.

* **Authentication**

    All requests include a keystone authentication token header
    (X-Auth-Token). Clients must authenticate with keystone before
    interacting with the murano service.