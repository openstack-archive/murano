.. _murano-agent:

============
Murano agent
============

Murano easily installs and configures necessary software on new virtual
machines. Murano agent is one of the main participants of these processes.

Usually, it is enough to execute a single script to install a simple
application. A more complex installation requires a deep script result
analysis. For example, we have a cross-platform application. The first script
determines the operation system and the second one calls an appropriate
installation script. Note, that installation script may be written in different
languages (the shell for Linux and PowerShell for Windows). Murano agent can
easily handle this situation and even more complicated ones.

So murano agent operates not with scripts, but with execution plans, which are
minimum units of the installation workflow.

Murano-agent on a new VM
~~~~~~~~~~~~~~~~~~~~~~~~

Earlier most of the application deployments were possible only on images with
pre-installed murano agent. You can refer to
:ref:`corresponding documentation <building_images>`
on building an image with murano-agent.

Currently murano-agent can be automatically installed by cloud-init. To deploy
an application on an image with pre-installed cloud-init you should mark the
image with Murano specific metadata. More information about preparing images
can be found :ref:`here <upload_images>`. This type of installation has some
limitations. The image has to have pre-installed python 2.7. Murano-agent is
installed from PyPi so the instance should have connectivity with the Internet.
Also it requires an installation of some python packages, e.g. python-pip,
python-dev, python-setuptools, python-virtualenv, which are also installed by
cloud-init.

Interaction with murano-engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First of all, communication between murano-agent and murano engine should be
established. The communication is performed through AMQP protocol. This type of
communication is preferable (for example, compared to SSH) because it is:

* Durable

  * To establish the connection, there is no need to wait until the
    instance is spawned. Murano-agent, on its turn, does not need
    to wait for a murano-engine task.

  * Messages can be sent to RabbitMQ asynchronously.

  * The connection does not depend on network issues. And moreover, there is no
    way to physically connect to the virtual machine if floating IP is not set.

  * It is possible to reload the instance and change network parameters during
    the deployment.

* Reliable

  If one instance of murano-engine fails in the middle of the deployment,
  another one picks up the messages from the queue and continue the deployment.

Right after application author calls the :command:`deploy` method of the class, inherited from
*io.murano.resources.Instance*, new murano-agent configuration file starts
forming in accordance with the values specified in the ``[rabbitmq]`` murano
configuration file section. A script that runs through cloud-init copies a
new file to the right place during the instance booting.


Execution plans and execution plan templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It was already mentioned that murano-agent recognizes execution plans.
These instructions contain scripts with all the required parameters
The application package author provides the execution plan templates together
with scripts code. During the deployment it is complemented with all required
parameters (including user-input).

For more information on execution plan templates, refer to
:ref:`Execution plan template <exec_plan>`.

Take a look at the muranoPL code snippet. The``EtcdAddMember`` template expects
*name* and *ip* parameters. The first line shows that these parameters are
passed to the template, and the second one shows that the template is sent to
the agent:

.. code-block:: console

  - $template: $resources.yaml('EtcdAddMember.template').bind(dict(
                name => $.instance.name,
                ip => $.getIp()
              ))
  - $clusterConfig: $._cluster.masterNode.instance.agent.call($template, $resources)

Beside the simple agent call, there is a method that enables sending an already
prepared execution plan (not a template). The main difference between template
and full execution plan is in the ``files`` section. Prepared execution plan contains
file contents and name by which they are reachable. So it is not required to
provide the resources argument:

.. code-block:: console

   ..instance.agent.callRaw($plan)

Also, there are ``instance.agent.call($template, $resources)`` and
``..instance.agent.sendRaw($plan)`` methods which have the same meaning but
indicate the engine not to wait for the script execution result. The default
agent call response time (with the corresponding method call) is set in
murano configuration file and equals to one hour. Take a look at the ``engine``
section:

.. code-block:: console

   [engine]
   # Time for waiting for a response from murano-agent during the
   # deployment (integer value)
   agent_timeout = 3600

.. note:: Murano-agent is able to run different types of scripts,
         such as powershell, python, bash, chef, and puppets. Moreover, it has
         a mechanism for extending supported formats and that is why murano
         agent is called ``unified``

To use puppet a deployment workflow, configure an execution plan as follows:

#. Set correct version of format:

   ``FormatVersion >=2.1.0``. Previous formats does not support puppet execution.

#. Use corresponding type

   In the script section, script item should have ``Type: Puppet``

#. Provide entry-point class

   Use puppet syntax ``EntryPoint: mysql::server``


.. note:: You can use scripts directly from git or svn repositories:

   .. code-block:: console

      Files:
       -  mysql: https://github.com/nanliu/puppet-staging.git

A script output is available in the murano-agent log file. This file is located
on the spawned instance at :file:`/etc/murano/agent.conf` on a Linux-based
machine, or :file:`C:\\Murano\\Agent\\agent.conf` on a Windows-based machine.
You can also refer to murano-agent log if there is no connectivity with
murano-engine (check if RabbitMQ settings are updated) or to track
deployment execution.
