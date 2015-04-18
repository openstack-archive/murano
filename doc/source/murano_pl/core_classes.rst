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

.. _core_library:

=====================
MuranoPL Core Library
=====================

Some objects and actions could be used in several application deployments. All common parts are grouped into MuranoPL libraries.
Murano core library is a set of classes needed in every deployment. Class names from core library could be used in the application definitions.
This library is located under the `meta <http://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/>`_ directory.
The following classes are included into the Murano core library:

**io.murano:**

- :ref:`Object`
- :ref:`Application`
- :ref:`SecurityGroupManager`
- :ref:`Environment`

**io.murano.resources:**

- :ref:`Instance`

    :ref:`Resources <Instance_resources>`:

    - Agent-v1.template
    - Agent-v2.template
    - linux-init.sh
    - windows-init.sh
- :ref:`Network`

**io.murano.lib.networks.neutron:**

- :ref:`NewNetwork`

.. _Object:

Class: Object
=============

Parent class for all MuranoPL classes, which implements initialize method, and setAttr and getAttr methods, which are defined in the pythonic part of the Object class.
All MuranoPL classes are implicitly inherited from this class.

.. _Application:

Class: Application
==================

Defines application itself. All custom applications should be derived from this class.
Has two properties:

.. code-block:: yaml

    Namespaces:
        =: io.murano

    Name: Application

    Workflow:
      reportDeployed:
          Arguments:
            - title:
                Contract: $.string()
                Default: null
            - unitCount:
                Contract: $.int()
                Default: null
          Body:
            - $this.find(Environment).instanceNotifier.trackApplication($this, $title, $unitCount)

      reportDestroyed:
          Body:
            - $this.find(Environment).instanceNotifier.untrackApplication($this)


.. _SecurityGroupManager:

Class: SecurityGroupManager
===========================

Manages  security groups during application deployment.

.. code-block:: yaml

    Namespaces:
        =: io.murano.system
        std: io.murano

    Name: SecurityGroupManager

    Properties:
      environment:
        Contract: $.class(std:Environment).notNull()

      defaultGroupName:
        Contract: $.string()
        Usage: Runtime
        Default: format('MuranoSecurityGroup-{0}', $.environment.name)

    Workflow:
      addGroupIngress:
        Arguments:
          - rules:
              Contract:
                - FromPort: $.int().notNull()
                  ToPort: $.int().notNull()
                  IpProtocol: $.string().notNull()
                  External: $.bool().notNull()
          - groupName:
              Contract: $.string().notNull()
              Default: $this.defaultGroupName
        Body:
          - $ext_keys:
              true:
                ext_key: remote_ip_prefix
                ext_val: '0.0.0.0/0'
              false:
                ext_key: remote_mode
                ext_val: remote_group_id

          - $stack: $.environment.stack
          - $template:
              Resources:
                $groupName:
                  Type: 'OS::Neutron::SecurityGroup'
                  Properties:
                    description: format('Composite security group of Murano environment {0}', $.environment.name)
                    rules:
                      - port_range_min: null
                        port_range_max: null
                        protocol: icmp
                        remote_ip_prefix: '0.0.0.0/0'
          - $.environment.stack.updateTemplate($template)

          - $ingress: $rules.select(dict(
                port_range_min => $.FromPort,
                port_range_max => $.ToPort,
                protocol => $.IpProtocol,
                $ext_keys.get($.External).ext_key => $ext_keys.get($.External).ext_val
              ))

          - $template:
              Resources:
                $groupName:
                  Type: 'OS::Neutron::SecurityGroup'
                  Properties:
                    rules: $ingress
          - $.environment.stack.updateTemplate($template)


.. _Environment:

Class: Environment
==================

Defines an Environment in terms of deployments process. Groups all the Applications and their related infrastructure, able to deploy them at once.
Environments is intent to group applications to manage them easily.

- *name* - an environment name
- *applications* - list of applications belonging to an environment
- *agentListener* -  property containing a ' :ref:`io.murano.system.AgentListener` object, which may be used to interact with Murano Agent
- *stack* - a property containing a HeatStack object which may be used to interact with the Heat Service
- *instanceNotifier* - a property containing a :ref:`io.murano.system.InstanceNotifier` which may be used to keep track of the amount of deployed instances
- *defaultNetworks* - a property containing user-defined Networks (:ref:`io.murano.resources.Network <Network>`), which may be used as the default networks for the Instances in this environment
- *securityGroupManager*- a property containing a :ref:`SecurityGroupManager <SecurityGroupManager>` object, which may be used to construct a security group associated with this environment

.. code-block:: yaml

    Namespaces:
        =: io.murano
        res: io.murano.resources
        sys: io.murano.system

    Name: Environment

    Properties:
      name:
        Contract: $.string().notNull()

      applications:
        Contract: [$.class(Application).owned().notNull()]

      agentListener:
        Contract: $.class(sys:AgentListener)
        Usage: Runtime

      stack:
        Contract: $.class(sys:HeatStack)
        Usage: Runtime

      instanceNotifier:
        Contract: $.class(sys:InstanceNotifier)
        Usage: Runtime

      defaultNetworks:
        Contract:
          environment: $.class(res:Network)
          flat: $.class(res:Network)
        Usage: In

      securityGroupManager:
        Contract: $.class(sys:SecurityGroupManager)
        Usage: Runtime

    Workflow:
      initialize:
        Body:
          - $this.agentListener: new(sys:AgentListener, name => $.name)
          - $this.stack: new(sys:HeatStack, name => $.name)
          - $this.instanceNotifier: new(sys:InstanceNotifier, environment => $this)
          - $this.reporter: new(sys:StatusReporter, environment => $this)
          - $this.securityGroupManager: new(sys:SecurityGroupManager, environment => $this)


      deploy:
        Body:
          - $.agentListener.start()
          - If: len($.applications) = 0
            Then:
              - $.stack.delete()
            Else:
              - $.applications.pselect($.deploy())
          - $.agentListener.stop()

.. _Instance:

Class: Instance
===============

Defines virtual machine parameters and manage instance lifecycle: spawning, deploying, joining to the network, applying security group and destroying.

- *name* - instance name
- *flavor* - instance flavor, defining virtual machine 'hardware' parameters
- *image* - instance image, defining operation system
- *keyname* - key pair name, used to make connect easily to the instance; optional
- *agent* - configures interaction with Murano Agent using :ref:`MuranoPL system class <io.murano.system.Agent>`
- *ipAddresses* - list of all IP addresses, assigned to an instance
- *networks* - configures type of networks, to which instance will be joined.
   Custom networks, that extends :ref:`Network class <Network>` could be specified and an instance will be connected to them
   and for a default environment network or flat network if corresponding values are set to true;
   without additional configurations, instance will be joined to the default network that are set in the current environment.
- *assignFloatingIp* - determines, if floating IP need to be assigned to an instance, default is false
- *floatingIpAddress* - IP addresses, assigned to an instance after an application deployment
- *securityGroupName* - security group, to which instance will be joined, could be set; optional

.. code-block:: yaml

    Namespaces:
      =: io.murano.resources
      std: io.murano
      sys: io.murano.system

    Name: Instance

    Properties:
      name:
        Contract: $.string().notNull()
      flavor:
        Contract: $.string().notNull()
      image:
        Contract: $.string().notNull()
      keyname:
        Contract: $.string()
        Default: null

      agent:
        Contract: $.class(sys:Agent)
        Usage: Runtime
      ipAddresses:
        Contract: [$.string()]
        Usage: Out
      networks:
        Contract:
          useEnvironmentNetwork: $.bool().notNull()
          useFlatNetwork: $.bool().notNull()
          customNetworks: [$.class(Network).notNull()]
        Default:
          useEnvironmentNetwork: true
          useFlatNetwork: false
          customNetworks: []
      assignFloatingIp:
        Contract: $.bool().notNull()
        Default: false
      floatingIpAddress:
        Contract: $.string()
        Usage: Out
      securityGroupName:
        Contract: $.string()
        Default: null

    Workflow:
      initialize:
        Body:
          - $.environment: $.find(std:Environment).require()
          - $.agent: new(sys:Agent, host => $)
          - $.resources: new(sys:Resources)

      deploy:
        Body:
          - $securityGroupName: coalesce(
                $.securityGroupName,
                $.environment.securityGroupManager.defaultGroupName
              )
          - $.createDefaultInstanceSecurityGroupRules($securityGroupName)

          - If: $.networks.useEnvironmentNetwork
            Then:
              $.joinNet($.environment.defaultNetworks.environment, $securityGroupName)
          - If: $.networks.useFlatNetwork
            Then:
              $.joinNet($.environment.defaultNetworks.flat, $securityGroupName)
          - $.networks.customNetworks.select($this.joinNet($, $securityGroupName))

          - $userData: $.prepareUserData()

          - $template:
              Resources:
                $.name:
                  Type: 'AWS::EC2::Instance'
                  Properties:
                    InstanceType: $.flavor
                    ImageId: $.image
                    UserData: $userData
                    KeyName: $.keyname

              Outputs:
                format('{0}-PublicIp', $.name):
                  Value:
                    - Fn::GetAtt: [$.name, PublicIp]
          - $.environment.stack.updateTemplate($template)
          - $.environment.stack.push()
          - $outputs: $.environment.stack.output()
          - $.ipAddresses: $outputs.get(format('{0}-PublicIp', $this.name))
          - $.floatingIpAddress: $outputs.get(format('{0}-FloatingIPaddress', $this.name))
          - $.environment.instanceNotifier.trackApplication($this)

      joinNet:
        Arguments:
          - net:
              Contract: $.class(Network)
          - securityGroupName:
              Contract: $.string()
        Body:
          - If: $net != null
            Then:
              - If: $.assignFloatingIp and (not bool($.getAttr(fipAssigned)))
                Then:
                  - $assignFip: true
                  - $.setAttr(fipAssigned, true)
                Else:
                  - $assignFip: false
              - $net.addHostToNetwork($, $assignFip, $securityGroupName)

      destroy:
        Body:
          - $template: $.environment.stack.current()
          - $patchBlock:
              op: remove
              path: format('/Resources/{0}', $.name)
          - $template: patch($template, $patchBlock)
          - $.environment.stack.setTemplate($template)
          - $.environment.stack.push()
          - $.environment.instanceNotifier.untrackApplication($this)

      createDefaultInstanceSecurityGroupRules:
        Arguments:
          - groupName:
              Contract: $.string().notNull()
        Body:

          - If: !yaql "'w' in toLower($.image)"
            Then:
              - $rules:
                  - ToPort: 3389
                    IpProtocol: tcp
                    FromPort: 3389
                    External: true
            Else:
              - $rules:
                  - ToPort: 22
                    IpProtocol: tcp
                    FromPort: 22
                    External: true
          - $.environment.securityGroupManager.addGroupIngress(
              rules => $rules, groupName => $groupName)

      getDefaultSecurityRules:
      prepareUserData:
        Body:
          - If: !yaql "'w' in toLower($.image)"
            Then:
              - $configFile: $.resources.string('Agent-v1.template')
              - $initScript: $.resources.string('windows-init.ps1')
            Else:
              - $configFile: $.resources.string('Agent-v2.template')
              - $initScript: $.resources.string('linux-init.sh')

          - $configReplacements:
              "%RABBITMQ_HOST%": config(rabbitmq, host)
              "%RABBITMQ_PORT%": config(rabbitmq, port)
              "%RABBITMQ_USER%": config(rabbitmq, login)
              "%RABBITMQ_PASSWORD%": config(rabbitmq, password)
              "%RABBITMQ_VHOST%": config(rabbitmq, virtual_host)
              "%RABBITMQ_SSL%": str(config(rabbitmq, ssl)).toLower()
              "%RABBITMQ_INPUT_QUEUE%": $.agent.queueName()
              "%RESULT_QUEUE%": $.environment.agentListener.queueName()

          - $scriptReplacements:
              "%AGENT_CONFIG_BASE64%": base64encode($configFile.replace($configReplacements))
              "%INTERNAL_HOSTNAME%": $.name
              "%MURANO_SERVER_ADDRESS%": coalesce(config(file_server), config(rabbitmq, host))
              "%CA_ROOT_CERT_BASE64%": ""

          - Return: $initScript.replace($scriptReplacements)

.. _Instance_resources:

Instance class uses the following resources:

- *Agent-v2.template* - Python Murano Agent template (This agent is unified and lately, Windows Agent will be included into it)
- *linux-init.sh* - Python Murano Agent initialization script, which sets up an agent with valid information, containing in                                                 updated agent template.
- *Agent-v1.template* - Windows Murano Agent template
- *windows-init.sh* -  Windows Murano Agent initialization script

.. _Network:

Class: Network
==============

Base abstract class for all MuranoPL classes, representing networks.

.. code-block:: yaml

    Namespaces:
        =: io.murano.resources

    Name: Network

    Workflow:
      addHostToNetwork:
        Arguments:
          - instance:
              Contract: $.class(Instance).notNull()
          - assignFloatingIp:
              Contract: $.bool().notNull()
              Default: false
          - securityGroupName:
              Contract: $.string()
              Default: null

.. _NewNetwork:

Class: NewNetwork
=================

Defining network type, using in Neutron.

- *name* - network name
- *autoUplink* - defines auto uplink network parameter; optional, turned on by default
- *autogenerateSubnet* - defines auto subnet generation; optional, turned on by default
- *subnetCidr* - CIDR, defining network subnet, optional
- *dnsNameserver* - DNS server name, optional
- *useDefaultDns* - defines ether set default DNS or not, optional, turned on by default

.. code-block:: yaml

    Namespaces:
      =: io.murano.lib.networks.neutron
      res: io.murano.resources
      std: io.murano
      sys: io.murano.system

    Name: NewNetwork

    Extends: res:Network

    Properties:
      name:
        Contract: $.string().notNull()

      externalRouterId:
        Contract: $.string()
        Usage: InOut

      autoUplink:
        Contract: $.bool().notNull()
        Default: true

      autogenerateSubnet:
        Contract: $.bool().notNull()
        Default: true

      subnetCidr:
        Contract: $.string()
        Usage: InOut

      dnsNameserver:
        Contract: $.string()
        Usage: InOut

      useDefaultDns:
        Contract: $.bool().notNull()
        Default: true

    Workflow:
      initialize:
        Body:
          - $.environment: $.find(std:Environment).require()
          - $.netExplorer: new(sys:NetworkExplorer)

      deploy:
        Body:
          - $.ensureNetworkConfigured()
          - $.environment.instanceNotifier.untrackApplication($this)

      addHostToNetwork:
        Arguments:
          - instance:
              Contract: $.class(res:Instance).notNull()
          - assignFloatingIp:
              Contract: $.bool().notNull()
              Default: false
          - securityGroupName:
              Contract: $.string()
              Default: null
        Body:
          - $.ensureNetworkConfigured()
          - $portname: $instance.name + '-port-to-' + $.id()
          - $template:
              Resources:
                $portname:
                  Type: 'OS::Neutron::Port'
                  Properties:
                    network_id: {Ref: $.net_res_name}
                    fixed_ips: [{subnet_id: {Ref: $.subnet_res_name}}]
                    security_groups:
                      - Ref: $securityGroupName
                $instance.name:
                  Properties:
                    NetworkInterfaces:
                      - Ref: $portname
          - $.environment.stack.updateTemplate($template)

          - If: $assignFloatingIp
            Then:
              - $extNetId: $.netExplorer.getExternalNetworkIdForRouter($.externalRouterId)
              - If: $extNetId != null
                Then:
                  - $fip_name: $instance.name + '-FloatingIP-' + $.id()
                  - $template:
                      Resources:
                        $fip_name:
                          Type: 'OS::Neutron::FloatingIP'
                          Properties:
                            floating_network_id: $extNetId
                        $instance.name + '-FloatingIpAssoc-' + $.id():
                          Type: 'OS::Neutron::FloatingIPAssociation'
                          Properties:
                            floatingip_id:
                              Ref: $fip_name
                            port_id:
                              Ref: $portname
                      Outputs:
                        $instance.name + '-FloatingIPaddress':
                          Value:
                            Fn::GetAtt:
                              - $fip_name
                              - floating_ip_address
                          Description: Floating IP assigned
                  - $.environment.stack.updateTemplate($template)

      ensureNetworkConfigured:
        Body:
          - If: !yaql "not bool($.getAttr(networkConfigured))"
            Then:
              - If: $.useDefaultDns and (not bool($.dnsNameserver))
                Then:
                  - $.dnsNameserver: $.netExplorer.getDefaultDns()

              - $.net_res_name: $.name + '-net-' + $.id()
              - $.subnet_res_name: $.name + '-subnet-' + $.id()
              - $.createNetwork()
              - If: $.autoUplink and (not bool($.externalRouterId))
                Then:
                  - $.externalRouterId: $.netExplorer.getDefaultRouter()
              - If: $.autogenerateSubnet and (not bool($.subnetCidr))
                Then:
                  - $.subnetCidr: $.netExplorer.getAvailableCidr($.externalRouterId, $.id())
              - $.createSubnet()
              - If: !yaql "bool($.externalRouterId)"
                Then:
                  - $.createRouterInterface()

              - $.environment.stack.push()
              - $.setAttr(networkConfigured, true)


      createNetwork:
        Body:
          - $template:
              Resources:
                $.net_res_name:
                  Type: 'OS::Neutron::Net'
                  Properties:
                    name: $.name
          - $.environment.stack.updateTemplate($template)

      createSubnet:
        Body:
          - $template:
              Resources:
                $.subnet_res_name:
                  Type: 'OS::Neutron::Subnet'
                  Properties:
                    network_id: {Ref: $.net_res_name}
                    ip_version: 4
                    dns_nameservers: [$.dnsNameserver]
                    cidr: $.subnetCidr
          - $.environment.stack.updateTemplate($template)

      createRouterInterface:
        Body:
          - $template:
              Resources:
                $.name + '-ri-' + $.id():
                  Type: 'OS::Neutron::RouterInterface'
                  Properties:
                    router_id: $.externalRouterId
                    subnet_id: {Ref: $.subnet_res_name}
          - $.environment.stack.updateTemplate($template)
