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

=====================================
Murano TroubleShooting and Debug Tips
=====================================

During installation and setting environment of new projects (tenants) you 
can run into different problems. This section intends to reduce the time 
spent on the solution of these problems.

Problems during configuration
=============================

Log location
++++++++++++

*Murano* is a multi component project, there several places where logs could be found.

The location of the log file completely depends on the setting in the config file of the corresponding component.
*log_file* parameter points to the log file, and if it's omitted or commented logging will be sent to stdout.


Possible problem list
+++++++++++++++++++++++

* `murano-db-manage` failed to execute

  * Check `connection` parameter in provided config file. It should be a `connection string <http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html>`_.

* Murano Dashboard is not working

  * Make sure, that *prepare_murano.sh* script was executed and *murano* file located in *enabled* folder under openstack_dashboard repository.
  * Check, that murano data is not inserted twice in the settings file and as a plugin.


Problems during deployment
==========================

Besides identifying errors from log files, there is another and more flexible way to browse deployment errors - directly from UI.
After *Deploy Failed* status is appeared navigate to environment components and open *Deployment History* page.
Click on the *Show details* button located at the corresponding deployment row of the table. Then go to the *Logs* tab.
You can see steps of the deployments and the one that failed would have red color.

*  Deployment freeze after ``Begin execution: io.murano.system.Agent.call`` problem with connection between Murano Agent and spawned instance.

  * Need to check transport access to the virtual machine (check router has gateway).
  * Check for rabbitMq settings: verify that agent has been obtained valid rabbit parameters.
    Go to the spawned virtual machine and open */etc/murano/agent.conf* or *C:\Murano\Agent\agent.conf* on Windows-based machine.
    Also, you can examine agent logs, located by default at */var/log/murano-agent.log*
    The first part of the log file will contain reconnection attempts to the rabbit - since the valid rabbit address and queue have not been obtained yet.
  * Check that *driver* option is set to `messagingv2`
  * Check that linux image name is not starts with 'w' letter

*  ``[exceptions.EnvironmentError]: Unexpected stack state NOT_FOUND`` - problem with heat stack creation, need to examine Heat log file.
   If you are running the deployment on a new tenant check that the router exists and it has gateway to the external network.
*  ``Router could not be created, no external network found`` - Find `external_network` parameter in config file and check
   that specified external network is really exist via UI or by executing `openstack network list --external` command.
*  ``NoPackageForClassFound: Package for class io.murano. Environment is not found`` - Check that murano core package is uploaded.
   If no, the content of `meta/io.murano` folder should be zipped and uploaded to Murano.
