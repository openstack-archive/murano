..
      Copyright 2015 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _app_migrate_to_juno:


Migrate applications from Murano v0.5 to Stable/Juno
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Applications created for murano v0.5, unfortunately, are not supported in Murano
stable/juno. This document provides the application code changes required for
compatibility with the stable/juno murano version.

Rename *'Workflow'* to *'Methods'*
----------------------------------

In stable/juno the name of section containing class methods is renamed to
*Methods*, as the latter is more OOP and doesn't cause confusion with Mistral. So,
you need to change it in *app.name/Classes* in all classes describing workflow
of your app.

For example:

::

    Workflow:
      deploy:
        Body:
          - $._environment.reporter.report($this, 'Creating VM')

Should be changed to:

::

    Methods:
      deploy:
        Body:
          - $._environment.reporter.report($this, 'Creating VM')

Change the Instance type in the UI definition 'Application' section
-------------------------------------------------------------------

The Instance class was too generic and contained some dirty workarounds to
differently handle Windows and Linux images, to bootstrap an instance in a
number of ways, etc. To solve these problems more classes were added to the
*Instance* inheritance hierarchy.

Now, base *Instance* class is abstract and agnostic of the desired OS and agent
type. It is inherited by two classes: *LinuxInstance* and *WindowsInstance*.

- *LinuxInstance* adds a default security rule for Linux, opening a standard
  SSH port;

- *WindowsInstance* adds a default security rule for Windows, opening an RDP
  port. At the same time WindowsInstance prepares a user-data allowing to use
  Murano v1 agent.

*LinuxInstance* is inherited by two other classes, having different software
config method:

- *LinuxMuranoInstance* adds a user-data preparation to configure Murano
  v2 agent;

- *LinuxUDInstance* adds a custom user-data field allowing the services to
  supply their own user data.

You need to specify the instance type which is required by your app. It
specifies a field in UI, where user can select an image matched to the instance
type. This change must be added to UI form definition in *app.name/UI/ui.yaml*.

For example, if you are going to install your application on Ubuntu, you need to
change:

::

  Application:
    ?:
    instance:
      ?:
        type: io.murano.resources.Instance

to:

::

  Application:
    ?:
    instance:
      ?:
        type: io.murano.resources.LinuxMuranoInstance

