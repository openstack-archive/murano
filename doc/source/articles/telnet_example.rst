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
..
.. _telnet-example:

Telnet Example
--------------

.. code-block:: yaml

    Namespaces:
      =: io.murano.apps.linux
      std: io.murano
      res: io.murano.resources


    Name: Telnet

    # Inheritance from io.murano.Application class
    # (located at Murano Core library) indicates,
    # that this is a complete application
    # and that 'deploy' method has to be defined.
    Extends: std:Application

    Properties:
      name:
        Contract: $.string().notNull()

      instance:
        Contract: $.class(res:Instance).notNull()


    Methods:
      deploy:
        Body:
          # Determine the environment to which the application belongs.
          # This message will be stored in deployment logs and available in UI
          - $this.find(std:Environment).reporter.report($this, 'Creating VM for Telnet instace.')
          # Deploy VM
          - $.instance.deploy()
          - $this.find(std:Environment).reporter.report($this, 'Instance is created. Setup Telnet service.')
          # Create instance of murano resource class. Agent will use it to find
          # corresponding execution plan by the file name
          - $resources: new('io.murano.system.Resources')
          # Deploy Telnet
          - $template: $resources.yaml('DeployTelnet.template')
          # Send prepared execution plan to Murano agent
          - $.instance.agent.call($template, $resources)
          - $this.find(std:Environment).reporter.report($this, 'Telnet service setup is done.')
