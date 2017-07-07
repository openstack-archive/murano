MS Windows image builder for OpenStack Murano
=============================================

Introduction
------------

This repository contains MS Windows templates, powershell scripts and bash scripted logic used to create qcow2 images
for QEMU/KVM based virtual machines used in OpenStack.

MS Windows Versions
-------------------

Supported by builder versions with en_US localization:

* Windows 2012 R2
* Windows 2012 R2 Core
* Windows 2008 R2
* Windows 2008 R2 Core

Getting Started
---------------

Trial versions of Windows 2008 R2 / 2012 R2 used by default. You could use these images for 180 days without activation.
You could download evaluation versions from official Microsoft website:

* `[Windows 2012 R2 - download] <https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2012-r2>`_
* `[Windows 2008 R2 - download] <https://www.microsoft.com/en-us/download/details.aspx?id=11093>`_

System requirements
~~~~~~~~~~~~~~~~~~~

* Debian based Linux distribution, like Ubuntu, Mint and so on.
* Packages required:
  ``qemu-kvm virt-manager virt-goodies virtinst bridge-utils libvirt-bin
  uuid-runtime samba samba-common cifs-utils``
* User should be able to run sudo without password prompt!

  .. code-block:: console

    sudo echo "${USER}    ALL = NOPASSWD: ALL" > /etc/sudoers.d/${USER}
    sudo chmod 440 /etc/sudoers.d/${USER}

* Free disk space > 50G on partition where script will spawn virtual machines because of ``40G`` required by virtual
  machine HDD image.
* Internet connectivity.
* Samba shared resource.

Configuring builder
~~~~~~~~~~~~~~~~~~~

Configuration parameters to tweak:

``[default]``

* ``workdir`` - place where script would prepare all software required by build scenarios. By `default` is not set,
  i.e. script directory would used as root of working space.
* ``vmsworkdir`` - must contain valid path, this parameter tells script where it should spawn virtual machines.
* ``runparallel`` - *true* of *false*, **false** set by default. This parameter describes how to start virtual machines,
  one by one or in launch them in background.

``[samba]``

* ``mode`` - *local* or *remote*. In local mode script would try to install and configure Samba server locally. If set
  to remote, you should also provide information about connection.
* ``host`` - in local mode - is 192.168.122.1, otherwise set proper ip address.
* ``user`` - set to **guest** by default in case of guest rw access.
* ``domain`` - Samba server user domain, if not set `host` value used.
* ``password`` - Samba server user password.
* ``image-builder-share`` - Samba server remote directory.

MS Windows install preparation:

``[win2k12r2]`` or ``[win2k8r2]`` - shortcuts for 2012 R2 and 2008 R2.

* ``enabled`` - *true* of *false*, include or exclude release processing by script.
* ``editions`` - standard, core or both(space used as delimiter).
* ``iso`` - local path to iso file

By default ``[win2k8r2]`` - disabled, if you need you can enable this release in *config.ini* file.

Run
---

Preparation
~~~~~~~~~~~

Run ``chmod +x *.sh`` in builder directory to make script files executable.

Command line parameters:
~~~~~~~~~~~~~~~~~~~~~~~~

``runme.sh`` - the main script

* ``--help`` - shows usage
* ``--forceinstall-dependencies`` - Runs dependencies install.
* ``--check-smb`` - Run checks or configuration of Samba server.
* ``--download-requirements`` - Download all required and configures software except MS Windows ISO.
* ``--show-configured`` - Shows configured and available to use MS Windows releases.
* ``--run`` - normal run

Experimental options:
^^^^^^^^^^^^^^^^^^^^^

* ``--config-file`` - Set configuration file location instead of default.

Use cases
---------

All examples below describes changes in ``config.ini`` file

1. I want to build one image for specific version and edition. For example: version - **2012 R2** and edition -
   **standard**. Steps to reach the goal:

 * Disable ``[win2k8r2]`` from script processing.

   .. code-block:: ini

    [win2k8r2]
    enabled=false

 - Update ``[win2k12r2]`` with desired edition(**standard**).

   .. code-block:: ini

     [win2k12r2]
     enabled=true
     editions=standard

 * Execute ``runme.sh --run``

2. I want to build two images for specific version with all supported by script editions. For example: **2012 R2** and
   editions - **standard** and **core**. Steps to reach the goal:

 * Disable `[win2k8r2]` from script processing.

   .. code-block:: ini

     [win2k8r2]
     enabled=false

 * Update ``[win2k12r2]`` with desired editions(**standard** and **core**).

   .. code-block:: ini

     [win2k12r2]
     enabled=true
     editions=standard core


 * Execute ``runme.sh --run``

3. I want to build two images for all supported by script versions with specific editions. For example: versions -
   **2012 R2** and **2008 R2** and edition - **core**. Steps to reach the goal:

 * Update ``[win2k8r2]`` with desired edition(**core**).

   .. code-block:: ini

      [win2k8r2]
      enabled=true
      editions=core

 * Update ``[win2k12r2]`` with desired edition(**core**).

   .. code-block:: ini

      [win2k12r2]
      enabled=true
      editions=core

 * Execute ``runme.sh --run``

