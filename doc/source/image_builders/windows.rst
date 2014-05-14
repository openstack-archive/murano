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

Murano requires a Windows Image in QCOW2 format to be builded and
uploaded into Glance.

The easiest way to build Windows image for Murano is to build it on the
host where your OpenStack is installed.

Install Required Packages
=========================

    **Note**

    Please check that hardware virtualization supported and enabled in
    BIOS.

The following packages should be installed on any host which will be
used to build Windows Image:

* ipxe-qemu
* kvm-ipxe
* qemu-kvm
* munin-libvirt-plugins
* python-libvirt
* virt-goodies
* virt-manager
* virt-top
* virt-what
* virtinst
* python

On Ubuntu you could install them using the command below:

::

    ># apt-get install ipxe-qemu kvm-ipxe qemu-kvm virt-goodies \
               virtinst virt-manager libvirt0 libvirt-bin \
               munin-libvirt-plugins python python-libvirt \
               python-libxml2 python-minimal python-pycurl \
               python-pyorbit python-requests python-six \
               samba samba-common openssh-server virt-top virt-what


Configure Shared Resource
=========================

**Configure samba based share.**

::

    ># mkdir -p /opt/samba/share
    ># chown -R nobody:nogroup /opt/samba/share

**Configure samba server (/etc/samba/smb.conf).**

::

    ...
    [global]
       ...
       security = user
    ...
    [share]
       comment = Deployment Share
       path = /opt/samba/share
       browsable = yes
       read only = no
       create mask = 0755
       guest ok = yes
       guest account = nobody
    ...

**Restart services.**

::

    ># service smbd restart
    ># service nmbd restart

Prerequisites
===============

Download the files below and copy them into their places in your
**${SHARE\_PATH}** folder (we usually use **/opt/samba/share** as
**${SHARE\_PATH}**):

* *Windows 2012 Server ISO evaluation version*

  * ${SHARE\_PATH}/libvirt/images/ws-2012-eval.iso
  * `http://technet.microsoft.com/en-us/evalcenter/hh670538.aspx`_

* *VirtIO drivers for Windows*

  * ${SHARE\_PATH}/libvirt/images/virtio-win-0.1-74.iso
  * `http://alt.fedoraproject.org/pub/alt/virtio-win/stable/virtio-win-0.1-74.iso`_

* *CloudBase-Init for Windows*

  * ${SHARE\_PATH}/share/files/CloudbaseInitSetup\_Beta.msi
  * `https://www.cloudbase.it/downloads/CloudbaseInitSetup_Beta.msi`_

* *Far Manager*

  * ${SHARE\_PATH}/share/files/Far30b3367.x64.20130717.msi
  * `http://www.farmanager.com/files/Far30b3525.x64.20130717.msi`_

* Git client

  * ${SHARE\_PATH}/share/files/Git-1.8.1.2-preview20130601.exe
  * `https://msysgit.googlecode.com/files/Git-1.8.3-preview20130601.exe`_

* *Sysinternals Suite*

  * ${SHARE\_PATH}/share/files/SysinternalsSuite.zip
  * `http://download.sysinternals.com/files/SysinternalsSuite.zip`_

* *unzip.exe tool*

  * ${SHARE\_PATH}/share/files/unzip.exe
  * `https://www.dropbox.com/sh/zthldcxnp6r4flm/AACwiyfcrlGDt3ygCFHrbwMra/unzip.exe`_

* *PowerShell v3*

  * ${SHARE\_PATH}/share/files/Windows6.1-KB2506143-x64.msu
  * `http://www.microsoft.com/en-us/download/details.aspx?id=34595`_
* *.NET 4.0*

  * ${SHARE\_PATH}/share/files/dotNetFx40\_Full\_x86\_x64.exe
  * `http://www.microsoft.com/en-us/download/details.aspx?id=17718`_


* *.NET 4.5*

  * ${SHARE\_PATH}/share/files/dotNetFx45\_Full\_setup.exe
  * `http://www.microsoft.com/en-us/download/details.aspx?id=30653`_


* *Murano Agent*

  * ${SHARE\_PATH}/share/files/MuranoAgent.zip
  * `https://www.dropbox.com/sh/zthldcxnp6r4flm/AADh6LkVkcw2j8nKZevqedHja/MuranoAgent.zip`_


.. _`http://technet.microsoft.com/en-us/evalcenter/hh670538.aspx`: http://technet.microsoft.com/en-us/evalcenter/hh670538.aspx
.. _`http://alt.fedoraproject.org/pub/alt/virtio-win/stable/virtio-win-0.1-74.iso`: http://alt.fedoraproject.org/pub/alt/virtio-win/stable/virtio-win-0.1-74.iso
.. _`https://www.cloudbase.it/downloads/CloudbaseInitSetup_Beta.msi`: https://www.cloudbase.it/downloads/CloudbaseInitSetup_Beta.msi
.. _`http://www.farmanager.com/files/Far30b3525.x64.20130717.msi`: http://www.farmanager.com/files/Far30b3525.x64.20130717.msi
.. _`https://msysgit.googlecode.com/files/Git-1.8.3-preview20130601.exe`: https://msysgit.googlecode.com/files/Git-1.8.3-preview20130601.exe
.. _`http://download.sysinternals.com/files/SysinternalsSuite.zip`: http://download.sysinternals.com/files/SysinternalsSuite.zip
.. _`https://www.dropbox.com/sh/zthldcxnp6r4flm/AACwiyfcrlGDt3ygCFHrbwMra/unzip.exe`: https://www.dropbox.com/sh/zthldcxnp6r4flm/AACwiyfcrlGDt3ygCFHrbwMra/unzip.exe
.. _`http://www.microsoft.com/en-us/download/details.aspx?id=34595`: http://www.microsoft.com/en-us/download/details.aspx?id=34595
.. _`http://www.microsoft.com/en-us/download/details.aspx?id=17718`: http://www.microsoft.com/en-us/download/details.aspx?id=17718
.. _`http://www.microsoft.com/en-us/download/details.aspx?id=30653`: http://www.microsoft.com/en-us/download/details.aspx?id=30653
.. _`https://www.dropbox.com/sh/zthldcxnp6r4flm/AADh6LkVkcw2j8nKZevqedHja/MuranoAgent.zip`: https://www.dropbox.com/sh/zthldcxnp6r4flm/AADh6LkVkcw2j8nKZevqedHja/MuranoAgent.zip


Additional Software
===================

This section describes additional software which is required to build an
Windows Image.

**Windows ADK**

*Windows Assessment and Deployment Kit (ADK) for Windows® 8* is required
to build your own answer files for auto unattended Windows installation.

You can dowload it from `http://www.microsoft.com/en-us/download/details.aspx?id=30652`_.

**PuTTY**

PuTTY is a useful tool to manage your Linux boxes via SSH.

You can download it from
`http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html`_.

**Windows Server ISO image**

We use the following Windows installation images:

* Windows Server 2008 R2

  * Image Name:
               7601.17514.101119-1850\_x64fre\_server\_eval\_en-us-GRMSXEVAL\_EN\_DVD.iso
  * URL:
        `http://www.microsoft.com/en-us/download/details.aspx?id=11093`_

* Windows Server 2012

 * Image Name:
              9200.16384.WIN8\_RTM.120725-1247\_X64FRE\_SERVER\_EVAL\_EN-US-HRM\_SSS\_X64FREE\_EN-US\_DV5.iso
 * URL:
        `http://technet.microsoft.com/en-US/evalcenter/hh670538.aspx?ocid=&wt.mc\_id=TEC\_108\_1\_33`_


**VirtIO Red Hat drivers ISO image**

    **Warning**

    Please, choose stable version instead of latest, We’ve got errors
    with unstable drivers during guest unattended install.

Download drivers from
`http://alt.fedoraproject.org/pub/alt/virtio-win/stable/`_

**Floppy Image With Unattended File**

Run following commands as root:

1. Create emtpy floppy image in your home folder

   ::

       ># dd bs=512 count=2880 \
          if=/dev/zero of=~/floppy.img \
          mkfs.msdos ~/floppy.img

2. Mount the image to **/media/floppy**

   ::

       ># mkdir /media/floppy mount -o loop \
          ~/floppy.img /media/floppy

3. Download **autounattend.xml** file from
   `https://raw.githubusercontent.com/stackforge/murano-deployment/master/image-builder/share/files/ws-2012-std/autounattend.xml.template`_

   ::

    ># cd ~
    ># wget https://raw.githubusercontent.com/stackforge/murano-deployment/master/image-builder/share/files/ws-2012-std/autounattend.xml.template


4. Copy our **autounattend.xml** to **/media/floppy**

   ::

    ># cp ~/autounattend.xml /media/floppy

5. Unmount the image

   ::

    ># umount /media/floppy

.. _`http://www.microsoft.com/en-us/download/details.aspx?id=30652`: http://www.microsoft.com/en-us/download/details.aspx?id=30652
.. _`http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html`: http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html
.. _`http://www.microsoft.com/en-us/download/details.aspx?id=11093`: http://www.microsoft.com/en-us/download/details.aspx?id=11093
.. _`http://technet.microsoft.com/en-US/evalcenter/hh670538.aspx?ocid=&wt.mc\_id=TEC\_108\_1\_33`: http://technet.microsoft.com/en-US/evalcenter/hh670538.aspx?ocid=&wt.mc\_id=TEC\_108\_1\_33
.. _`http://alt.fedoraproject.org/pub/alt/virtio-win/stable/`: http://alt.fedoraproject.org/pub/alt/virtio-win/stable/
.. _`https://raw.githubusercontent.com/stackforge/murano-deployment/master/image-builder/share/files/ws-2012-std/autounattend.xml.template`: https://raw.githubusercontent.com/stackforge/murano-deployment/master/image-builder/share/files/ws-2012-std/autounattend.xml.template

Build Windows Image (Automatic Way)
===================================

1. Clone **murano-deployment** repository

   ::

       ># git clone git://github.com/stackforge/murano-deployment.git

2. Change directory to **murano-deployment/image-builder** folder.

3. Create folder structure for image builder

   ::

       ># make build-root

4. Create shared resource

   **Add to /etc/samba/smb.conf.**

   ::

       [image-builder-share]
          comment = Image Builder Share
          browsable = yes
          path = /opt/image-builder/share
          guest ok = yes
          guest user = nobody
          read only = no
          create mask = 0755

   **Restart samba services.**

   ::

       ># restart smbd && restart nmbd

5. Test that all required files are in place

   ::

       ># make test-build-files

6. Get list of available images

   ::

       ># make

7. Run image build process

   ::

       ># make ws-2012-std

8. Wait until process finishes

9. The image file **ws-2012-std.qcow2** should be stored under
**/opt/image-builder/share/images** folder.

Build Windows Image (Manual Way)
================================

    **Warning**

    Please note that the preferred way to build images is to use
    **Automated Build** described in the previous chapter.

**Get Post-Install Scripts**

There are a few scripts which perform all the required post-installation
tasks.

Package installation tasks are performed by script named **wpi.ps1**.

Download it from `https://raw.github.com/stackforge/murano-deployment/master/image-builder/share/scripts/ws-2012-std/wpi.ps1`_

    **Note**

    There are a few scripts named **wpi.ps1**, each supports only one
    version of Windows image. The script above is intended to be used to
    create Windows Server 2012 Standard. To build other version of
    Windows please use appropriate script from **scripts** folder.

Clean-up actions to finish image preparation are performed by
**Start-Sysprep.ps1** script.

Download it from `https://raw.github.com/stackforge/murano-deployment/master/image-builder/share/scripts/ws-2012-std/Start-Sysprep.ps1`_

These scripts should be copied to the shared resource folder, subfolder
**Scripts**.

**Create a VM**

This section describes steps required to build an image of Windows
Virtual Machine which could be used with Murano. There are two possible
ways to create it - from CLI or using GUI tools. We describe both in
this section.

    **Note**

    Run all commands as root.

**Way 1: Using CLI Tools**

This section describes the required step to launch a VM using CLI tools
only.

1. Preallocate disk image

   ::

       ># qemu-img create -f raw /var/lib/libvirt/images/ws-2012.img 40G

2. Start the VM

   ::

       ># virt-install --connect qemu:///system --hvm --name WinServ \
          --ram 2048 --vcpus 2 --cdrom /opt/samba/share/9200.16384.WIN8_RTM\
       .120725-1247_X64FRE_SERVER_EVAL_EN-US-HRM_SSS_X64FREE_EN-US_DV5.ISO \
         --disk path=/opt/samba/share/virtio-win-0.1-52.iso,device=cdrom \
         --disk path=/opt/samba/share/floppy.img,device=floppy \
         --disk path=/var/lib/libvirt/images/ws-2012.qcow2\
       ,format=qcow2,bus=virtio,cache=none \
         --network network=default,model=virtio \
         --memballoon model=virtio --vnc --os-type=windows \
         --os-variant=win2k8 --noautoconsole \
         --accelerate --noapic --keymap=en-us --video=cirrus --force

**Way 2: Using virt-manager UI**

A VM also could be lauched via GUI tools like virt-manager.

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

**Convert the image from RAW to QCOW2 format.**

The image must be converted from RAW format to QCOW2 before being
imported into Glance.

::

    ># qemu-img convert -O qcow2 /var/lib/libvirt/images/ws-2012.raw \
       /var/lib/libvirt/images/ws-2012-ref.qcow2

.. _`https://raw.github.com/stackforge/murano-deployment/master/image-builder/share/scripts/ws-2012-std/wpi.ps1`: https://raw.github.com/stackforge/murano-deployment/master/image-builder/share/scripts/ws-2012-std/wpi.ps1
.. _`https://raw.github.com/stackforge/murano-deployment/master/image-builder/share/scripts/ws-2012-std/Start-Sysprep.ps1`: https://raw.github.com/stackforge/murano-deployment/master/image-builder/share/scripts/ws-2012-std/Start-Sysprep.ps1
