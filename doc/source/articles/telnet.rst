..
      Copyright 2014 2014 Mirantis, Inc.

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

.. _TelnetUI:

===================================
UI Definition of telnet application
===================================

.. code-block:: yaml

    Version: 2

    Templates:
      instance:
        ?:
          type: io.murano.resources.LinuxMuranoInstance
        name: generateHostname($.appConfiguration.unitNamingPattern, 1)
        flavor: $.instanceConfiguration.flavor
        image: $.instanceConfiguration.osImage
        keyname: $.instanceConfiguration.keyPair
        assignFloatingIp: $.appConfiguration.assignFloatingIP

    Application:
      ?:
        type: io.murano.apps.linux.Telnet
      name: $.appConfiguration.name
      instance: $instance


    Forms:
      - appConfiguration:
          fields:
            - name: title
              type: string
              required: false
              hidden: true
              description: Telnet is a service that allows a Telnet client to connect across a network and access a command session
            - name: name
              type: string
              label: Application Name
              description: >-
                Enter a desired name for the application. Just A-Z, a-z, 0-9, dash and
                underline are allowed.
              minLength: 2
              maxLength: 64
              regexpValidator: '^[-\w]+$'
              errorMessages:
                invalid: Just letters, numbers, underscores and hyphens are allowed.
              helpText: Just letters, numbers, underscores and hyphens are allowed.
            - name: dcInstances
              type: integer
              hidden: true
              initial: 1
            - name: assignFloatingIP
              type: boolean
              label: Assign Floating IP
              description: >-
                 Select to true to assign floating IP automatically
              initial: false
              required: false
              widgetMedia:
                css: {all: ['muranodashboard/css/checkbox.css']}
            - name: unitNamingPattern
              type: string
              label: Hostname
              description: >-
                For your convenience instance hostname can be specified.
                Enter a name or leave blank for random name generation.
              required: false
              regexpValidator: '^(([a-zA-Z0-9#][a-zA-Z0-9-#]*[a-zA-Z0-9#])\.)*([A-Za-z0-9#]|[A-Za-z0-9#][A-Za-z0-9-#]*[A-Za-z0-9#])$'
              helpText: Optional field for a machine hostname
              # temporaryHack
              widgetMedia:
                js: ['muranodashboard/js/support_placeholder.js']
                css: {all: ['muranodashboard/css/support_placeholder.css']}
          validators:
            # if unitNamingPattern is given and dcInstances > 1, then '#' should occur in unitNamingPattern
            - expr: $.appConfiguration.dcInstances < 2 or not $.appConfiguration.unitNamingPattern.bool() or '#' in $.appConfiguration.unitNamingPattern
              message: Incrementation symbol "#" is required in the Hostname template
      - instanceConfiguration:
          fields:
            - name: title
              type: string
              required: false
              hidden: true
              description: Specify some instance parameters on which the application would be created
            - name: flavor
              type: flavor
              label: Instance flavor
              description: >-
                Select registered in OpenStack flavor. Consider that application performance
                depends on this parameter.
              required: false
            - name: osImage
              type: image
              imageType: linux
              label: Instance image
              description: >-
                Select valid image for the application. Image should have Murano agent installed and
                registered in Glance.
            - name: keyPair
              type: keypair
              label: Key Pair
              description: >-
                Select the Key Pair to control access to instances. You can login to
                instances using this KeyPair after application deployment
              required: false
            - name: availabilityZone
              type: azone
              label: Availability zone
              description: Select availability zone where the application would be installed.
              required: false

