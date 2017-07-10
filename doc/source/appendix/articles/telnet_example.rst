:orphan:

.. _telnet_example:

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
          - $this.find(std:Environment).reporter.report($this, 'Creating VM for Telnet Instance.')
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
