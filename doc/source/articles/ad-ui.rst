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

.. _adUI:

=============================================
UI Definition Of Active Directory Application
=============================================

.. code-block:: yaml

    Version: 2

    Templates:
      primaryController:
        ?:
          type: io.murano.windows.activeDirectory.PrimaryController
        host:
          ?:
            type: io.murano.windows.Host
          adminPassword: $.appConfiguration.adminPassword
          name: generateHostname($.appConfiguration.unitNamingPattern, 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage
          assignFloatingIp: $.appConfiguration.assignFloatingIP

      secondaryController:
        ?:
          type: io.murano.windows.activeDirectory.SecondaryController
        host:
          ?:
            type: io.murano.services.windows.Host
          adminPassword: $.appConfiguration.adminPassword
          name: generateHostname($.appConfiguration.unitNamingPattern, $index + 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage

    Application:
      ?:
        type: io.murano.windows.activeDirectory.ActiveDirectory
      name: $.appConfiguration.name
      primaryController: $primaryController
      secondaryControllers: repeat($secondaryController, $.appConfiguration.dcInstances - 1)

    Forms:
      - appConfiguration:
          fields:
            - name: configuration
              type: string
              hidden: true
              initial: standalone
            - name: name
              type: string
              label: Domain Name
              description: >-
                Enter a desired name for a new domain. This name should fit to
                DNS Domain Name requirements: it should contain
                only A-Z, a-z, 0-9, (.) and (-) and should not end with a dash.
                DNS server will be automatically set up on each of the Domain
                Controller instances. Note: Only first 15 characters or characters
                before first period is used as NetBIOS name.
              minLength: 2
              maxLength: 255
              validators:
                - expr:
                    regexpValidator: '^([0-9A-Za-z]|[0-9A-Za-z][0-9A-Za-z-]*[0-9A-Za-z])\.[0-9A-Za-z][0-9A-Za-z-]*[0-9A-Za-z]$'
                  message: >-
                    Only letters, numbers and dashes in the middle are
                    allowed. Period characters are allowed only when they
                    are used to delimit the components of domain style
                    names. Single-level domain is not
                    appropriate. Subdomains are not allowed.
                - expr:
                    regexpValidator: '(^[^.]+$|^[^.]{1,15}\..*$)'
                  message: >-
                    NetBIOS name cannot be shorter than 1 symbol and
                    longer than 15 symbols.
                - expr:
                    regexpValidator: '(^[^.]+$|^[^.]*\.[^.]{2,63}.*$)'
                  message: >-
                    DNS host name cannot be shorter than 2 symbols and
                    longer than 63 symbols.
              helpText: >-
                Just letters, numbers and dashes are allowed.
                A dot can be used to create subdomains
            - name: dcInstances
              type: integer
              label: Instance Count
              description: >-
                You can create several Active Directory instances by setting
                instance number larger than one. One primary Domain Controller
                and a few secondary DCs will be created.
              minValue: 1
              maxValue: 100
              initial: 1
              helpText: Enter an integer value between 1 and 100
            - name: adminAccountName
              type: string
              label: Account Name
              initial: Administrator
              regexpValidator: '^[-\w]+$'
              errorMessages:
                invalid: 'Just letters, numbers, underscores and hyphens are allowed.'
            - name: adminPassword
              type: password
              label: Administrator password
              descriptionTitle: Passwords
              description: >-
                Windows requires strong password for service administration.
                Your password should have at least one letter in each
                register, a number and a special character. Password length should be
                a minimum of 7 characters.

                Once you forget your password you won't be able to
                operate  the service until recovery password would be entered. So it's
                better for Recovery and Administrator password to be different.
            - name: recoveryPassword
              type: password
              label: Recovery password
            - name: assignFloatingIP
              required: false
              type: boolean
              label: Assign Floating IP
              description: >-
                 Select to true to assign floating IP automatically to Primary DC
              initial: false
              required: false
              widgetMedia:
                css: {all: ['muranodashboard/css/checkbox.css']}
            - name: unitNamingPattern
              type: string
              label: Hostname template
              description: >-
                For your convenience all instance hostnames can be named
                in the same way. Enter a name and use # character for incrementation.
                For example, host# turns into host1, host2, etc. Please follow Windows
                hostname restrictions.
              required: false
              regexpValidator: '^(([a-zA-Z0-9#][a-zA-Z0-9-#]*[a-zA-Z0-9#])\.)*([A-Za-z0-9#]|[A-Za-z0-9#][A-Za-z0-9-#]*[A-Za-z0-9#])$'
              # FIXME: does not work for # turning into 2-digit numbers
              maxLength: 15
              helpText: Optional field for a machine hostname template
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
              descriptionTitle: Instance Configuration
              description: Specify some instance parameters on which service would be created.
            - name: flavor
              type: flavor
              label: Instance flavor
              description: >-
                Select registered in Openstack flavor. Consider that service performance
                depends on this parameter.
              required: false
            - name: osImage
              type: image
              imageType: windows
              label: Instance image
              description: >-
                Select valid image for a service. Image should already be prepared and
                registered in glance.
            - name: availabilityZone
              type: azone
              label: Availability zone
              description: Select availability zone where service would be installed.
              required: false
