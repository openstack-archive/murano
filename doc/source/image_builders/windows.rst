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



=============
Windows Image
=============

Murano requires a Windows Image in QCOW2 format to be built and uploaded into Glance.

The easiest way to build Windows image for Murano is to build it on the host where your OpenStack is installed.



Prepare Image Builder Host
==========================


Install KVM
-----------

.. note::

  This guide was tested on Ubuntu Server 12.04 x64.
..

KVM is a default hypervisor in OpenStack, so our build scripts are targeted to this hypervisor only. It may change in future, though.

Install KVM and some additional packages that are required by our scripts

.. code-block:: console

  # apt-get install qemu-kvm virtinst virt-manager
..

Check that your hardware supports hardware virtualization.

.. code-block:: console

  $ kvm-ok
  INFO: /dev/kvm exists
  KVM acceleration can be used
..

If your output differs, check that harware virtualization is enabled in your BIOS settings. You also could try import KVM kernel module

.. code-block:: console

  $ sudo modprobe kvm-intel
..

or

.. code-block:: cosole

  $ sudo modprobe kvm-amd
..

It might be helpful to add an appropriate module name into **/etc/modules** file to auto-load it during system boot. Sometimes it is required on Ubuntu systems.



Configure Shared Resource
=========================

Murano Image Builder uses a shared folder located on the host system as an installation source for components.
Makefile from image builder will copy required files to their locations, but you have to manually configure samba share.
To do this, use the steps below.

* Install samba

  .. code-block:: console

    # apt-get install samba
  ..

* Create folder that will be shared

  .. code-block:: console

    # mkdir -p /opt/samba/share
    # chown -R nobody:nogroup /opt/samba/share
  ..

* Configure samba server (/etc/samba/smb.conf)

  .. code-block:: text
    :linenos:

    ...
    [global]
       ...
      security = share
      ...
    [image-builder-share]
        comment = Image Builder Share
        browsable = yes
        path = /opt/image-builder/share
        guest ok = yes
        guest user = nobody
        read only = no
        create mask = 0755
    ...
  ..

* Restart samba services

  .. code-block:: console

      # service smbd restart
      # service nmbd restart
  ..



Download Prerequisites
======================


.. _windows_installation_iso:

Windows Server Installation ISO
-------------------------------

.. list-table::
    :header-rows: 1
    :widths: 30, 15, 55

    * - Windows Version
      - Version String
      - Save to

    * - Windows Server 2008 R2 [#win2k8r2_link]_
      - 6.1.7601
      - /opt/image-builder/share/libvirt/images/ws-2008-eval.iso

    * - Windows Server 2012 [#win2k12_link]_
      - 6.3.9200
      - /opt/image-builder/share/libvirt/images/ws-2012-eval.iso
..

.. warning::

  Windows Server 2008 R2 must include Service Pack 1 updates. This is required to install PowerShell V3 which is required by Murano Agent.
..

|
.. [#win2k8r2_link] http://www.microsoft.com/en-us/download/details.aspx?id=11093
.. [#win2k12_link] http://technet.microsoft.com/en-US/evalcenter/hh670538.aspx?ocid=&wt.mc_id=TEC_108_1_33


.. _required_prerequisites:

Required Components
-------------------

.. list-table::
  :header-rows: 1
  :widths: 30, 70

  * - Component
    - Save to

  * - VirtIO drivers for Windows [#virtio_iso_link]_
    - /opt/image-builder/share/libvirt/images/virtio-win-0.1-74.iso

  * - CloudBase-Init for Windows [#cloudbase_init_link]_
    - /opt/image-builder/share/files/CloudbaseInitSetup_Beta.msi

  * - .NET 4.0 [#dot_net_40_link]_
    - /opt/image-builder/share/files/dotNetFx40_Full_x86_x64.exe

  * - PowerShell v3 [#powershell_v3_link]_
    - /opt/image-builder/share/files/Windows6.1-KB2506143-x64.msu

  * - Murano Agent [#murano_agent_link]_
    - /opt/image-builder/share/files/MuranoAgent.zip

  * - Git client [#msysgit_link]_
    - /opt/image-builder/share/files/Git-1.8.1.2-preview20130601.exe
..

.. warning::

  PowerShell V3 is a **mandatory** prerequisite. It is required by Murano Agent. To check your PowerShell version use PowerShell command *Get-Host*.
..

.. warning::

  When downloading VirtIO drivers choose only stable versions.
  Unstable versions might lead to errors during guest unattended installation.
  You can check the latest version avaible here: http://alt.fedoraproject.org/pub/alt/virtio-win/stable
..

|
.. [#ws2012iso_link] http://technet.microsoft.com/en-us/evalcenter/hh670538.aspx
.. [#virtio_iso_link] http://alt.fedoraproject.org/pub/alt/virtio-win/stable/virtio-win-0.1-74.iso
.. [#cloudbase_init_link] https://www.cloudbase.it/downloads/CloudbaseInitSetup_Beta.msi
.. [#dot_net_40_link] http://www.microsoft.com/en-us/download/details.aspx?id=17718
.. [#powershell_v3_link] http://www.microsoft.com/en-us/download/details.aspx?id=34595
.. [#murano_agent_link] https://www.dropbox.com/sh/zthldcxnp6r4flm/AADh6LkVkcw2j8nKZevqedHja/MuranoAgent.zip
.. [#msysgit_link] https://msysgit.googlecode.com/files/Git-1.8.3-preview20130601.exe


.. _optional_prerequisites:

Optional Components
-------------------

These components are not mandatory for Murano Agent to function properly.
However, they may help you work with the image after deployment.

.. list-table::
  :header-rows: 1
  :widths: 30, 70

  * - Component
    - Save to

  * - Far Manager [#far_manager_link]_
    - /opt/image-builder/share/files/Far30b3367.x64.20130717.msi

  * - Sysinternals Suite [#sysinternals_link]_
    - /opt/image-builder/share/files/SysinternalsSuite.zip

  * - unzip.exe [#unzip_link]_
    - /opt/image-builder/share/files/unzip.exe

  * - .NET 4.5 [#dot_net_45_link]_
    - /opt/image-builder/share/files/dotNetFx45_Full_setup.exe
..

|
.. [#far_manager_link] http://www.farmanager.com/files/Far30b3525.x64.20130717.msi
.. [#sysinternals_link] http://download.sysinternals.com/files/SysinternalsSuite.zip
.. [#unzip_link] https://www.dropbox.com/sh/zthldcxnp6r4flm/AACwiyfcrlGDt3ygCFHrbwMra/unzip.exe
.. [#dot_net_45_link] http://www.microsoft.com/en-us/download/details.aspx?id=30653





Additional Tools
================

Tools from this section are not necessary to build an image.
However, they may be helpful if you want to create an image with different configuration.


Windows Assessment and Deployment Kit (ADK)
-------------------------------------------

*Windows ADK* is required if you want to build your own answer files for auto unattended Windows installation.

Download it from http://www.microsoft.com/en-us/download/details.aspx?id=30652


Floppy Image With Unattended File
---------------------------------

Floppy image with answer file for unattended installation is needed to automate Windows installation process.

* Create emtpy floppy image in your home folder

  .. code-block:: console

    $ mkdir ~/flp/files
    $ mkdir ~/flp/mnt
  ..

  .. code-block:: console

    $ dd bs=512 count=2880 if=/dev/zero of=~/flp/floppy.img
    $ mkfs.msdos ~/flp/floppy.img
  ..

* Mount the image

  .. code-block:: console

      $ mkdir ~/flp/mnt
      $ sudo mount -o loop ~/floppy.img ~/flp/mnt
  ..

* Download **autounattend.xml.template** file from https://github.com/openstack/murano-deployment/tree/master/contrib/windows/image-builder/share/files

  This folder contains unatteded files for several Windows versions, choose one that matches your Windows version.

* Copy that file to mounted floppy image

  .. code-block:: console

      $ cp ~/autounattend.xml.template ~/flp/mnt/autounattend.xml
  ..

* Replace string **%_IMAGE_BUILDER_IP_%** in that file with **192.168.122.1**

* Unmount the image

  .. code-block:: console

      $ sudo umount ~/flp/mnt
  ..



Build Windows Image with Murano
===============================


.. _build_image_using_image_builder_scripts:

Build Windows Image Using Image Builder Script
----------------------------------------------

* Clone **murano-deployment** repository

  .. code-block:: console

    $ git clone git://git.openstack.org/cgit/openstack/murano-deployment.git
  ..

* Change directory to image-builder folder

  .. code-block:: console

    $ cd murano-deployment/contrib/windows/image-builder
  ..

* Create folder structure for image builder

  .. code-block:: console

    $ sudo make build-root
  ..

* Download build prerequisites, and copy them to correct folders

  * :ref:`windows_installation_iso`
  * :ref:`required_prerequisites`
  * :ref:`optional_prerequisites` (Optional)

* Test that all required files are in place

  .. code-block:: console

    $ sudo make test-build-files
  ..

* Get list of available images

  .. code-block:: console

    $ make
  ..

* Run image build process (e.g. to build Windows Server 2012)

  .. code-block:: console

    $ sudo make ws-2012-std
  ..

* Wait until process finishes

* The image file **ws-2012-std.qcow2** should be stored inside **/opt/image-builder/share/images** folder.



Build Windows Image Manualy
---------------------------

.. note::

  Please note that the preferred way to build images is to use Image Builder scripts, see :ref:`build_image_using_image_builder_scripts`
..


Get Post-Install Scripts
------------------------

There are a few scripts which perform all the required post-installation tasks.

They all are located in http://git.openstack.org/cgit/openstack/murano-deployment/tree/contrib/windows/image-builder/share/scripts


.. note::

  There are subfolders for each supported Windows Version.
  Choose one that matches Windows Version you are building.
..

This folder contains several scripts

.. list-table::
  :header-rows: 1
  :widths: 20, 80

  * - Script Name
    - Description

  * - wpi.ps1
    - Handles component installation and system configuration tasks

  * - Start-Sysprep.ps1
    - Prepares system to be syspreped (cleans log files, stops some services and so on), and starts sysprep

  * - Start-AtFirstBoot.ps1
    - Performes basic after-installation tasks
..


Download these scripts and save them into /opt/image-builder/share/scripts


Create a VM
-----------

Now you need a virtual machine instance. There are two possible ways to create it - using CLI or GUI tools. We describe both in this section.


Using CLI Tools
^^^^^^^^^^^^^^^

1. Preallocate disk image

  .. code-block:: console

    $ qemu-img create -f raw /var/lib/libvirt/images/ws-2012.img 40G
  ..

2. Start the VM

  .. code-block:: console

    # virt-install --connect qemu:///system --hvm --name WinServ \
    > --ram 2048 --vcpus 2 --cdrom /opt/samba/share/9200.16384.WIN8_RTM\
    >.120725-1247_X64FRE_SERVER_EVAL_EN-US-HRM_SSS_X64FREE_EN-US_DV5.ISO \
    > --disk path=/opt/samba/share/virtio-win-0.1-52.iso,device=cdrom \
    > --disk path=/opt/samba/share/floppy.img,device=floppy \
    > --disk path=/var/lib/libvirt/images/ws-2012.qcow2\
    >,format=qcow2,bus=virtio,cache=none \
    > --network network=default,model=virtio \
    > --memballoon model=virtio --vnc --os-type=windows \
    > --os-variant=win2k8 --noautoconsole \
    > --accelerate --noapic --keymap=en-us --video=cirrus --force
  ..


Using virt-manager UI
^^^^^^^^^^^^^^^^^^^^^

1. Launch *virt-manager* from shell as root

2. Set a name for VM and select Local install media

3. Add one cdrom and attach Windows Server ISO image to it

4. Select OS type **Windows**

5. Set CPU and RAM amount

6. Deselect option **Enable storage for this virtual machine**

7. Add second cdrom for ISO image with virtio drivers

8. Add a floppy drive and attach our floppy image to it

9. Add (or create new) HDD image with Disk bus **VirtIO** and storage format **RAW**

10. Set network device model **VirtIO**

11. Start installation process and open guest vm screen through **Console** button


Install OS
----------

Launch your virtual machine, connect to its virtual console and complete OS installation. At the end of this step you should have Windows Server system that you are able to log into.

Install Prerequisites and Murano
--------------------------------

* Create folders where Murano components will be installed

  .. list-table::
    :header-rows: 1
    :widths: 20, 80

    * - Path
      - Description

    * - C:\\Murano
      - Root directory for Murano

    * - C:\\Murano\\Agent
      - Murano Agent installation directory

    * - C:\\Murano\\Modules
      - PowerShell modules required by Murano

    * - C:\\Murano\\Scripts
      - PowerShell scrtips and other files required by Murano
  ..

* Open **Explorer** and navigate to **\\192.168.122.1\share** **192.168.122.1** is an IP address of KVM hypervisor assigned by default.

* Copy Murano Agent files into C:\Murano\Agent

* Copy CoreFunctions directory (entire directory!) into C:\Murano\Modules

* Install .NET 4.0

* Register Murano Agent

  .. code-block:: cmd

    > cd C:\Murano\Agent
    > .\WindowsMuranoAgent.exe /install
  ..

* Change PowerShell execution policy to less restricted

  .. code-block:: powershell

    Set-ExecutionPolicy RemoteSigned
  ..

* Register CoreFunctions modules

  .. code-block:: powershell

    Import-Module C:\Murano\Modules\CoreFunctions\CoreFunctions.psm1 -ArgumentList register
  ..

* Install CloudInit

* Run Sysprep

  .. code-block:: powershell

    C:\Murano\Scripts\Start-Sysprep.ps1 -BatchExecution
  ..

* Wait until sysprep phase finishes and system powers off.

Convert the image from RAW to QCOW2 format
------------------------------------------

The image must be converted from RAW format to QCOW2 before being imported into Glance.

.. code-block:: console

    # qemu-img convert -O qcow2 /var/lib/libvirt/images/ws-2012.raw \
    > /var/lib/libvirt/images/ws-2012-ref.qcow2
..
