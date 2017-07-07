..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http//www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _deploying-using-cli:

================================
Deploying environments using CLI
================================

The main tool for deploying murano environments is murano-dashboard. It is
designed to be easy-to-use and intuitive. But it is not the only tool you can
use to deploy a murano environment, murano CLI client also possesses required
functionality for the task. This is an advanced scenario, however, that
requires knowledge of :ref:`internal murano workflow <murano-workflow>`,
:ref:`murano object model <object-model>`, and
:ref:`murano environment <environment>` lifecycle.
This scenario is suitable for deployments without
horizon or deployment automation.


.. note::

    This is an advanced mechanism and you should use it only when you are
    confident in what you are doing. Otherwise, it is recommended that you use
    murano-dashboard.

Create an environment
~~~~~~~~~~~~~~~~~~~~~

The following command creates a new murano environment that is ready for
configuration. For convenience, this guide refers to environment ID as
``$ENV_ID``.

.. code-block:: console

  $ murano environment-create deployed_from_cli

  +----------------------------------+-------------------+---------------------+---------------------+
  | ID                               | Name              | Created             | Updated             |
  +----------------------------------+-------------------+---------------------+---------------------+
  | a66e5ea35e9d4da48c2abc37b5a9753a | deployed_from_cli | 2015-10-06T13:50:45 | 2015-10-06T13:50:45 |
  +----------------------------------+-------------------+---------------------+---------------------+

Create a configuration session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Murano uses configuration sessions to allow several users to edit and configure
the same environment concurrently. Most of environment-related commands
require the ``--session-id`` parameter. For convenience, this guide
refers to session ID as ``$SESS_ID``.

To create a configuration session, use the
:command:`murano environment-session-create $ENV_ID` command:

.. code-block:: console

  $ murano environment-session-create $ENV_ID

  +----------+----------------------------------+
  | Property | Value                            |
  +----------+----------------------------------+
  | id       | 5cbe7e561ffc484ebf11aabf83f9f4c6 |
  +----------+----------------------------------+


Add applications to an environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To manipulate environments object model from CLI, use the
:command:`environment-apps-edit` command:

.. code-block:: console

  $ murano environment-apps-edit --session-id $SESS_ID $ENV_ID object_model_patch.json

The :file:`object_model_patch.json` contains the ``jsonpatch`` object. This
object is applied to the ``/services`` key of the environment in question.
Below is an example of the :file:`object_model_patch.json` file content:

.. code-block:: json

    [
        { "op": "add", "path": "/-", "value":
            {
                "instance": {
                    "availabilityZone": "nova",
                    "name": "xwvupifdxq27t1",
                    "image": "fa578106-b3c1-4c42-8562-4e2e2d2a0a0c",
                    "keyname": "",
                    "flavor": "m1.small",
                    "assignFloatingIp": false,
                    "?": {
                        "type": "io.murano.resources.LinuxMuranoInstance",
                        "id": "===id1==="
                    }
                },
                "name": "ApacheHttpServer",
                "enablePHP": true,
                "?": {
                    "type": "com.example.apache.ApacheHttpServer",
                    "id": "===id2==="
                }
            }
        }
    ]

For convenience, the murano client replaces the ``"===id1==="``, ``"===id2==="``
(and so on) strings with UUIDs. This way you can ensure that object IDs
inside your object model are unique.
To learn more about jsonpatch, consult jsonpatch.com_ and `RFC 6902`_.
The :command:`environment-apps-edit` command fully supports jsonpatch.
This means that you can alter, add, or remove parts of your applications
object model.

Verify your object model
~~~~~~~~~~~~~~~~~~~~~~~~

To verify whether your object model is correct, check the environment by
running the :command:`environment-show` command with the
``--session-id`` parameter:

.. code-block:: console

   $ murano environment-show $ENV_ID --session-id $SESS_ID --only-apps

    [
      {
        "instance": {
          "availabilityZone": "nova",
          "name": "xwvupifdxq27t1",
          "assignFloatingIp": false,
          "keyname": "",
          "flavor": "m1.small",
          "image": "fa578106-b3c1-4c42-8562-4e2e2d2a0a0c",
          "?": {
            "type": "io.murano.resources.LinuxMuranoInstance",
            "id": "fc4fe975f5454bab99bb0e309249e2d2"
          }
        },
        "?": {
          "status": "pending",
          "type": "com.example.apache.ApacheHttpServer",
          "id": "69cdf10d31e64196b4de894e7ea4f1be"
        },
        "enablePHP": true,
        "name": "ApacheHttpServer"
      }
    ]


Deploy your environment
~~~~~~~~~~~~~~~~~~~~~~~

To deploy a session ``$SESS_ID`` of your environment, use the
:command:`murano environment-deploy` command:

.. code-block:: console

   $ murano environment-deploy $ENV_ID --session-id $SESS_ID

You can later use the :command:`murano environment-show` command to
track the deployment status.

To view the deployed applications of a particular environment, use the
:command:`murano environment-show` command with the ``--only-apps``
parameter and specifying the environment ID:

.. code-block:: console

   $ murano environment-show $ENV_ID --only-apps

.. _jsonpatch.com: http://jsonpatch.com
.. _RFC 6902: http://tools.ietf.org/html/rfc6902
