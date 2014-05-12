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

===========
Linux Image
===========

**Create a VM**

This section describes steps required to build an image of Linux Virtual
Machine which could be used with Murano. There are two possible ways to
create it - from CLI or using GUI tools. We describe both in this
section.

    **Note**

    Run all commands as root.

**Way 1: Using CLI Tools**

This section describes the required step to launch a VM using CLI tools
only.

1. Preallocate disk image

   ::

       ># qemu-img create -f qcow2 /var/lib/libvirt/images/cloud-linux.img 10G


2. Start the VM

   ::

       ># virt-install --connect qemu:///system --hvm --name cloud-linux \
         --ram 2048 --vcpus 2 --cdrom /PATH_TO_YOUR_LINUX.ISO \
         --disk path=/var/lib/libvirt/images/cloud-linux.img, \
         format=qcow2,bus=virtio,cache=none \
         --network network=default,model=virtio \
         --memballoon model=virtio --vnc --os-type=linux \
         --accelerate --noapic --keymap=en-us --video=cirrus --force

**Way 2: Using virt-manager UI**

A VM also could be lauched via GUI tools like virt-manager.

1.  Launch *virt-manager* from shell as root

2.  Set a name for VM and select Local install media

3.  Add one cdrom and attach your linux ISO image to it

4.  Select OS type **Linux** and it's version **choose yours**

5.  Set CPU and RAM amount

6.  Deselect option **Enable storage for this virtual machine**

7.  Select option **Customize configuration before install**

8.  Add (or create new) HDD image with Disk bus **VirtIO** and storage
    format **QCOW2**

9.  Set network device model **VirtIO**

10. Start installation process and open guest vm screen through
    **Console** button

Guest VM Linux OS preparation
=============================

**Ubuntu 12.04 LTS x86\_64**

::

    ># for action in update upgrade dist-upgrade;do apt-get -y $action;done
    ># apt-get install -y git unzip make cmake gcc python-dev python-pip openssh-server sudo


**CentOS 6.4 x86\_64**

::

    ># rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
    ># for action in update upgrade;do yum -y $action; done
    ># yum install -y git unzip make cmake gcc python-devel python-pip openssh-server openssh-clients sudo


**murano-agent installation steps**

::

    ># mkdir -p /opt/git
    ># cd /opt/git
    ># git clone https://github.com/stackforge/murano-agent.git
    ># cd murano-agent/python-agent
    ># git checkout release-0.5
    ># chmod a+x setup*.sh

    # To install Murano Agent on run the following command:
    -  **Ubuntu**
       ># ./setup.sh install
    -  **CentOS**
       ># ./setup-centos.sh install


**cloud-init installation steps**

-  **Ubuntu**

   ::

       ># apt-get install -y cloud-init cloud-initramfs-growroot


-  **CentOS**

   ::

       ># yum install -y cloud-init


       **Note**

       **Ubuntu only**

       ::

           ># dpkg-reconfigure cloud-init


       Mark **EC2** data source support, save and exit or add manualy
       **Ec2** to the datasource\_list variable in the
       /etc/cloud/cloud.cfg.d/90\_dfkg.cfg

-  **Minimal cloud-init configuration options**

   ::

       ># vi /etc/cloud/cloud.cfg:
           user: ec2-user
           disable_root: 1
           preserve_hostname: False


**Security setup**

Create user and make it able to run commands through sudo without
password prompt.

-  **Ubuntu**

   ::

       ># useradd -m -G sudo -s /bin/bash ec2-user
       ># passwd ec2-user


-  **CentOS**

   ::

       ># useradd -m -G wheel -s /bin/bash ec2-user
       ># passwd ec2-user


-  **Sudo**

   ::

       ># echo "ec2-user   ALL=(ALL)  NOPASSWD: ALL" > /etc/sudoers.d/ec2-user
       ># chmod 440 /etc/sudoers.d/ec2-user

**Disable SSH password-based logins in the /etc/ssh/sshd\_config.**

::

    ...
    GSSAPIAuthentication no
    PasswordAuthentication no
    PermitRootLogin no
    ...


</itemizedlist> </para>
**Network handling**

-  **Ubuntu**

   ::

       ># rm -rf /etc/udev/rules.d/70-persistent-net.rules


-  **CentOS** Remove or comment out HWADDR and UUID in
   /etc/sysconfig/network-scripts/ifcfg-eth\*

   ::

       ># rm -rf /etc/udev/rules.d/70-persistent-net.rules


**Shutdown VM**

**Convert the image from RAW to QCOW2 format if you made it as RAW.**

The image must be converted from RAW format to QCOW2 before being
imorted into Glance.

::

    ># qemu-img convert -O qcow2 /var/lib/libvirt/images/cloud-linux.img \
    /var/lib/libvirt/images/cloud-linux.img.qcow2

