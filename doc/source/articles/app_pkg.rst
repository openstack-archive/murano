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

.. _app_pkg:

====================================
Composing application package manual
====================================

Murano is Application catalog that supports types of applications. This document intends to make composing application packages easily.

Step 1.  Prepare Execution Plans
================================

An *Execution Plan* is a set of metadata that describes the installation process of an application in a virtual machine.
It's a minimal unit of execution that can be triggered in Murano Workflows and should be understandable by Murano agent. From *Execution plans* any script can be triggered.
It could be any type of scripts which will execute commands and install application components as the result. Each script may consist of one or more files.
Scripts may be reused across several Execution Plans. One of the scripts should be an entry point and should be specified in a resource template file in *Scripts*.
Besides the *Scripts* section the following sections must be presented in a resource template file:

* **FormatVersion** - version of *Execution Plan* syntax format
* **Version** - version of *Execution Plan*
* **Name** -  human-readable name of the Execution Plan
* **Parameters** - parameters received from MuranoPL
* **Body** - Python statement, should start with | symbol
* **Scripts** - dictionary that maps script names to script definitions.

    Scripts are the building blocks of Execution Plans and they may be executed as a whole (like a single piece of code), expose some functions that can be independently called in scripts. This depends on Deployment Platform and Executor capabilities. One script can be defined with the following properties

    * **Type** Deployment Platform name that script is targeted to.
    * **Version** optional minimum version of deployment platform/executor required by the script.
    * **EntryPoint** relative path to the file that contains a script entry point
    * **Files** This is an optional array of additional files required for the script. Use *<>* to specify a relative path to the file. The root directory is *Resource/scripts*.
    * **Options** an optional argument of type contains additional options

.. _Telnet Agent:

Example *DeployTelnet.template*

.. code-block:: yaml

    FormatVersion: 2.0.0
    Version: 1.0.0
    Name: Deploy Telnet

    Parameters:
      appName: $appName

    Body: |
      return deploy(args.appName).stdout

    Scripts:
      deploy:
        Type: Application
        Version: 1.0.0
        EntryPoint: deployTelnet.sh
        Files:
          - installer.sh
          - common.sh
        Options:
          captureStdout: true
          captureStderr: false


Step 2.  Prepare MuranoPL class definitions
===========================================

MuranoPL classes control application deployment workflow execution. Full information about MuranoPL classes see here: :ref:`MuranoPL Spec`

.. _Telnet Class:

Example *telnet.yaml*

.. code-block:: yaml

    Namespaces:
      =: io.murano.apps.linux
      std: io.murano
      res: io.murano.resources


    Name: Telnet

    Extends: std:Application

    Properties:
      name:
        Contract: $.string().notNull()

      instance:
        Contract: $.class(res:Instance).notNull()


    Workflow:
      deploy:
        Body:
          - $this.find(std:Environment).reporter.report($this, 'Creating VM for Telnet instace.')
          - $.instance.deploy()
          - $this.find(std:Environment).reporter.report($this, 'Instance is created. Setup Telnet service.')
          - $resources: new('io.murano.system.Resources')
          # Deploy Telnet
          - $template: $resources.yaml('DeployTelnet.template')
          - $.instance.agent.call($template, $resources)
          - $this.find(std:Environment).reporter.report($this, 'Telnet service setup is done.')


Note, that

* *io.murano.system.Resources* is a system class, defined in MuranoPL. More information about MuranoPL system classes is available here: :ref:`class_definitions`.
* *io.murano.resources.Instance* is a class, defined in the core Murano library, which is available here. :ref:`This library <core_library>` contains Murano Agent templates and virtual machine initialization scripts.
* $this.find(std:Environment).reporter.report($this, 'Creating VM for Telnet instance.') - this is the way of sending reports to Murano dashboard during deployment

Step 3.  Prepare dynamic UI form definition
===========================================

Create a form definition in a yaml format. Before configuring a form, compose a list of parameters that will be required to set by a user.
Some form fields that are responsible for choosing a flavor, image and availability zone are better to use in every application creation wizard.
Syntax of  Dynamic UI can be found see at the corresponding section: :ref:`Dynamic UI Definition specification <DynamicUISpec>`.
Full example with Telnet application form definition :ref:`Telnet Definition <TelnetUI>`.

Step 4.  Prepare application logo
=================================

Find or create a simple image (in a .png format) associated with your application. Is should be small and have a square shape. You can specify any name of your image. In our example, let's name it *telnet.png*.

Step 5.  Prepare manifest file
==============================

General application metadata should be described in the application manifest file. It should be in a yaml format and should have the following sections

* **Format** - version of a manifest syntax format
* **Type** - package type. Valid choices are *Library* and *Application*
* **Name** - human-readable application name
* **Description** - a brief description of an application
* **Author** - person or company name which created an application package
* **Classes** - MuranoPL class list, on which application deployment is based
* **Tags** - list of words, associated with this application. Will be helpful during the search. *Optional* parameter
* **Require** - list of applications with versions, required by this application. Currently only used by repository importing mechanism. *Optional* parameter

.. _Telnet Manifest:

Example *manifest.yaml*

.. code-block:: yaml

    Format: 1.0
    Type: Application
    FullName: io.murano.apps.linux.Telnet
    Name: Telnet
    Description: |
     Telnet is the traditional protocol for making remote console connections over TCP.
    Author: 'Mirantis, Inc'
    Tags: [Linux, connection]
    Classes:
     io.murano.apps.linux.Telnet: telnet.yaml
    UI: telnet.yaml
    Logo: telnet.png
    Require:
      io.murano.apps.TelnetHelper: 0.0.1

Step 6.  Prepare images.lst file
================================

This step is optional. If you plan on providing images required by your
application, you can include ``images.lst`` file with image specifications

Example *images.lst*

.. code-block:: yaml

    Images:
    - Name: 'my_image.qcow2'
      Hash: '64d7c1cd2b6f60c92c14662941cb7913'
      Meta:
        title: 'tef'
        type: 'linux'
      DiskFormat: qcow2
      ContainerFormat: bare
    - Name: 'my_other_image.qcow2'
      Hash: '64d7c1cd2b6f60c92c14662941cb7913'
      Meta:
        title: 'tef'
        type: 'linux'
      DiskFormat: qcow2
      ContainerFormat: bare
      Url: 'http://path.to/images/file.qcow2'

If *Url* is omitted - the images would be searched for in the Murano Repository.

Step 7.  Compose a zip archive
==============================

An application archive should have the following structure

* *Classes* folder
    MuranoPL class definitions should be put inside this folder
* *Resources* folder
    This folder should contain Execution scripts

  * *Scripts* folder
       All script files, needed for an application deployment should be placed here

* *UI* folder
    Place dynamic ui yaml definitions here or skip to use the default name *ui.yaml*
* *logo.png*
    Image file should be placed in the root folder. It can have any name, just specify it in the manifest file or skip to use default *logo.png* name
* *manifest.yaml*
    Application manifest file. It's an application entry point. The file name is fixed.
* *images.lst*
    List of required images. Optional file.

Congratulations! Your application is ready to be uploaded to an Application Catalog.
