.. _actions:

==============
Murano actions
==============

Murano action is a type of MuranoPL method. The differences from a regular
MuranoPL method are:

* Action is executed on deployed objects.
* Action execution is initiated by API request, you do not have to call
  the method manually.

So murano action allows performing any operations on objects:

* Getting information from the VM, like a config that is generated during the
  deployment
* VM rebooting
* Scaling

A list of available actions is formed during the environment deployment.
Right after the deployment is finished, you can call action asynchronously.
Murano engine generates a task for every action. Therefore, the action status
can be tracked.

.. note::
 Actions may be called against any MuranoPL object, including ``Environment``,
 ``Application``, and any other objects.

.. note::
 Now murano doesn't support big files download during action execution. This is
 because action results are stored in murano database and are limited by
 approximately 10kb size.

To mark a method as an action, use ``Scope: Public`` or ``Usage: Action``.
The latter option is deprecated for the package format versions > 1.3 and
occasionally will be no longer supported. Also, you cannot use both
``Usage: Action`` and ``Scope: Session`` in one method.

The following example shows an action that returns an archive with a
configuration file:

.. code-block:: yaml

 exportConfig:
     Scope: Public
     Body:
       - $._environment.reporter.report($this, 'Action exportConfig called')
       - $resources: new(sys:Resources)
       - $template: $resources.yaml('ExportConfig.template')
       - $result: $.masterNode.instance.agent.call($template, $resources)
       - $._environment.reporter.report($this, 'Got archive from Kubernetes')
       - Return: new(std:File, base64Content => $result.content,
                     filename => 'application.tar.gz')

List of available actions can be found with environment details or application
details API calls. It's located in object model special data.
Take a look at the following example:

Request:
``http://localhost:8082/v1/environments/<id>/services/<id>``

Response:

.. code-block:: json

    {
      "name": "SimpleVM",
      "?": {
        "_26411a1861294160833743e45d0eaad9": {
          "name": "SimpleApp"
        },
        "type": "com.example.Simple",
        "id": "e34c317a-f5ee-4f3d-ad2f-d07421b13d67",
        "_actions": {
          "e34c317a-f5ee-4f3d-ad2f-d07421b13d67_exportConfig": {
            "enabled": true,
            "name": "exportConfig"
          }
        }
      }
    }


==============
Static actions
==============

Static methods (:ref:`static_methods_and_properties`) can also be called
through the API if they are exposed by specifying ``Scope: Public``, and the
result of its execution will be returned.

Consider the following example of the static action that makes use both of
static class property and user's input as an argument:

.. code-block:: yaml

 Name: Bar

 Properties:
   greeting:
     Usage: Static
     Contract: $.string()
     Default: 'Hello, '

 Methods:
   staticAction:
     Scope: Public
     Usage: Static
     Arguments:
       - myName:
           Contract: $.string().notNull()
     Body:
       - Return: concat($.greeting, $myName)

Request:
``http://localhost:8082/v1/actions``

Request body:

.. code-block:: json

    {
      "className": "ns.Bar",
      "methodName": "staticAction",
      "parameters": {"myName": "John"}
    }

Responce:

.. code-block:: json

   "Hello, John"
