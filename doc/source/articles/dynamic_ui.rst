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

.. _Dynamic UI Spec:

===================================
Dynamic UI Definition specification
===================================

The main purpose of Dynamic UI is to generate application creation forms "on-the-fly".
 Murano dashboard doesn't know anything about what applications can be deployed and which web form are needed to create application instance.
 So all application definitions should contain a yaml file which tells dashboard how to create an application and what validations are to be applied.
 This document will help you to compose a valid UI definition for your application.

Structure
=========

UI definition should be a valid yaml file and should contain the following sections (for version 2):

* **Version** - points out to which syntax version is used, optional
* **Templates** - optional, auxiliary section, used together with an Application section, optional
* **Application** - object model description which will be used for application deployment, required
* **Forms** - web form definitions, required

Version
=======

Version of supported dynamic UI syntax. The latest version is 2.
This is optional section, default version is set to 1.
Version mapping:
Murano 0.4 - version 1
Murano 0.5 - version 2

Application and Templates
=========================
In the Application *application object model* section is described. This model will be translated into json and according to that json application will be deployed.
Application section should contain all necessary keys that are required by murano-engine to deploy an application. Note that under ''?'' section goes system part of the model.
You can pick parameters you got from the user (they should be described in the Forms section) and pick the right place where they should be set.
To do this `YAQL <https://github.com/tsufiev/yaql/blob/master/README.md>`_ is used. All lines are going to be checked for a yaql expressions. Thus, *generateHostname* will be recognized as yaql function and will generate machine hostname .

*Example:*

.. code-block:: yaml

     primaryController:
        ?:
          type: io.murano.windows.activeDirectory.PrimaryController
        host:
          ?:
            type: io.murano.windows.Host
          adminPassword: $.serviceConfiguration.adminPassword
          name: generateHostname($.serviceConfiguration.unitNamingPattern, 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage

      secondaryController:
        ?:
          type: io.murano.windows.activeDirectory.SecondaryController
        host:
          ?:
            type: io.murano.windows.Host
          adminPassword: $.serviceConfiguration.adminPassword
          name: generateHostname($.serviceConfiguration.unitNamingPattern, $index + 1)
          flavor: $.instanceConfiguration.flavor
          image: $.instanceConfiguration.osImage

Forms
=====

This section describes Django forms. Set name for your form and provide fields and validators.
Each field should contain:

* **name** -  system field name, could be any
* **label** - name, that will be displayed in the form
* **description** - description, that will be displayed in the form description area. Use  yaml line folding character >- to keep the correct formatting during data transferring.
* **type** - system field type

    * string - Django string field
    * boolean - Django boolean field
    * text - Django boolean field
    * integer - Django integer field
    * password - Specific field with validation for strong password
    * clusterip - Specific field, used for cluster IP
    * domain - Specific field, used for Active Directory domain
    * databaselist - Specific field, a list of databases (comma-separated list of database names, where each name has the following syntax first symbol should be latin letter or underscore; subsequent symbols can be Latin letter, numeric, underscore, at the sign, number sign or dollar sign)
    * table - Specific field, used for defining table in a form
    * flavor - Specific field, used for defining flavor in a form
    * keypair - Specific field, used for defining KeyPair in a form
    * image- Specific field, used for defining image in a form
    * azone - Specific field, used for defining availability zone in a form

*Example*

.. code-block:: yaml

    Forms:
      - serviceConfiguration:
          fields:
            - name: name
              type: string
              label: Service Name
              description: >-
                To identify your service in logs please specify a service name
            - name: dcInstances
              type: integer
              hidden: true
              initial: 1
              required: false
              maxLength: 15
              helpText: Optional field for a machine hostname template
      - instanceConfiguration:
              fields:
                - name: flavor
                  type: flavor
                  label: Instance flavor
                  description: >-
                    Select registered in Openstack flavor. Consider that service performance
                    depends on this parameter.
                  required: false
                - name: osImage
                  type: image
                  imageType: linux
                  label: Instance image
                  description: >-
                    Select valid image for a service. Image should already be prepared and
                    registered in glance.
                - name: availabilityZone
                  type: azone
                  label: Availability zone
                  description: Select availability zone where service would be installed.
                  required: false

Full example with Telnet application form definitions is available here :ref:`telnet-yaml`
