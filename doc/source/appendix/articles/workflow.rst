.. _murano-workflow:

===============
Murano workflow
===============
What happens when a component is being created in an environment? This document
will use the Telnet package referenced elsewhere as an example. It assumes the
package has been previously uploaded to Murano.


Step 1.  Begin deployment
=========================
The API sends a message that instructs murano-engine, the workflow component of
Murano, to deploy an environment. The message consists of a JSON document
containing the class types required to create the environment, as well as any
parameters the user selected prior to deployment. Examples are:

* An :ref:`Environment` object (io.murano.Environment) with a *name*
* An object (or objects) referring to networks that need to be created
  or that already exist
* A list of Applications (e.g. io.murano.apps.linux.Telnet). Each Application
  will contain, or will reference, anything it requires. The Telnet example,
  has a property called *instance* whose contract states it must be of type
  io.murano.resources.Instance. In turn the Instance has properties it requires
  (like a name, a flavor, a keypair name).

Each object in this *model* has an ID so that the state of each can be tracked.

The classes that are required are determined by the application's manifest. In
the :ref:`Telnet example <telnet_example>` only one class is explicitly
required; the telnet application definition.

The :ref:`Telnet class definition <telnet_example>` refers to several other
classes. It extends :ref:`Application` and it requires an :ref:`Instance`.
It also refers to the :ref:`Environment` in which it will be contained,
sends reports through the environment's :ref:`status-reporter`
and adds security group rules to the :ref:`security-group-manager`.


Step 2.  Load definitions
=========================
The engine makes a series of requests to the API to download packages it
needs. These requests pass the class names the environment will require, and
during this stage the engine will validate that all the required classes exist
and are accessible, and will begin creating them. All Classes whose *workflow*
sections contain an *initialize* fragment are then initialized. A typical initialization
order would be (defined by the ordering in the *model* sent to the murano-engine):

* :ref:`Network`
* :ref:`Instance`
* :ref:`Object`
* :ref:`Environment`


Step 3.   Deploy resources
==========================
The workflow defined in Environment.deploy is now executed. The first step
typically is to initialize the messaging component that will pay attention
to murano-agent (see later). The next stage is to deploy each application the
environment knows about in turn, by running deploy() for each application.
This happens concurrently for all the applications belonging to an instance.

In the :ref:`Telnet example <telnet_example>` (under *Workflow*), the workflow
dictates sending a status message (via the environment's *reporter*, and
configuring some security group rules. It is at this stage that the engine
first contacts Heat to request information about any pre-existing resources
(and there will be none for a fresh deploy) before updating the new Heat
template with the security group information.

Next it instructs the engine to deploy the  *instance* it relies on. A large
part of the interaction with Heat is carried out at this stage; the first
thing an Instance does is add itself to the environment's network. Since the
network doesn't yet exist, murano-engine runs the neutron network workflow
which pushes template fragments to Heat. These fragments can define:
* Networks
* Subnets
* Router interfaces

Once this is done the Instance itself constructs a Heat template fragment and
again pushes it to Heat. The Instance will include a *userdata* script that
is run when the instance has started up, and which will configure and run
murano-agent.


Step 4.  Software configuration via murano-agent
================================================
If the workflow includes murano-agent components (and the telnet example does),
typically the application workflow will execute them as the next step.

In the telnet example, the workflow instructs the engine to load
*DeployTelnet.yaml* as YAML, and pass it to the murano-agent running on the
configured instance. This causes the agent to execute the *EntryPoint* defined
in the agent script (which in this case deploys some packages and sets some
iptables rules).


Step 5.  Done
=============
After execution is finished, the engine sends a last message indicating that
fact; the API receives it and marks the environment as deployed.
