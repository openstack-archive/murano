..
      Copyright 2014 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

========================
Prepare A Lab For Murano
========================
This section provides basic information about lab's system requirements.
It also contains a description of a test which you may use to check if
your hardware fits the requirements. To do this, run the test and
compare the results with baseline data provided.

System prerequisites
=====================
**Supported Operating Systems**

* Ubuntu Server 12.04 LTS
* RHEL/CentOS 6.4

**System packages are required for Murano**

*Ubuntu*

* gcc

* python-pip

* python-dev

* libxml2-dev

* libxslt-dev

* libffi-dev

* libpq-dev

* python-openssl

* mysql-client

*CentOS*

* gcc

* python-pip

* python-devel

* libxml2-devel

* libxslt-devel

* libffi-devel

* postgresql-devel

* pyOpenSSL

* mysql


Lab Requirements
================

+------------+--------------------------------+----------------------+
| Criteria   | Minimal                        | Recommended          |
+============+================================+======================+
| CPU        | 4 core @ 2.4 GHz               | 24 core @ 2.67 GHz   |
+------------+--------------------------------+----------------------+
| RAM        | 8 GB                           | 24 GB or more        |
+------------+--------------------------------+----------------------+
| HDD        | 2 x 500 GB (7200 rpm)          | 4 x 500 GB (7200 rpm |
+------------+--------------------------------+----------------------+
| RAID       | Software RAID-1 (use mdadm as  | Hardware RAID-10     |
|            | it will improve read           |                      |
|            | performance almost two times)  |                      |
+------------+--------------------------------+----------------------+

Table: Hardware requirements

There are a few possible storage configurations except the shown above.
All of them were tested and were working well.

* 1x SSD 500+ GB

* 1x HDD (7200 rpm) 500+ GB and 1x SSD 250+ GB (install the system onto
   the HDD and mount the SSD drive to folder where VM images are)

* 1x HDD (15000 rpm) 500+ GB

Test Your Lab Host Performance
==============================

We have measured time required to boot 1 to 5 instances of Windows
system simultaneously. You can use this data as the baseline to check if
your system is fast enough.

You should use sysprepped images for this test, to simulate VM first
boot.

Steps to reproduce test:

1. Prepare Windows 2012 Standard (with GUI) image in QCOW2 format. Let's
   assume that its name is ws-2012-std.qcow2

2. Ensure that there is NO KVM PROCESSES on the host. To do this, run
   command:

   ::

       ps aux | grep kvm

3. Make 5 copies of Windows image file:

   ::

       for i in $(seq 5); do \
       cp ws-2012-std.qcow2 ws-2012-std-$i.qcow2; done

4. Create script start-vm.sh in the folder with .qcow2 files:

   ::

       #!/bin/bash
       [ -z $1 ] || echo "VM count not provided!"; exit 1
       for i in $(seq $1); do
       echo "Starting VM $i ..."
       kvm -m 1024 -drive file=ws-2012-std-$i.qcow2,if=virtio -net user -net nic,model=virtio -nographic -usbdevice tablet -vnc :$i & done

5. Start ONE instance with command below (as root) and measure time
   between VM’s launch and the moment when Server Manager window
   appears. To view VM’s desktop, connect with VNC viewer to your host
   to VNC screen :1 (port 5901):

   ::

       sudo ./start-vm.sh 1

6. Turn VM off. You may simply kill all KVM processes by

   ::

       sudo killall kvm

7. Start FIVE instances with command below (as root) and measure time
   interval between ALL VM’s launch and the moment when LAST Server Manager
   window appears. To view VM’s desktops, connect with VNC viewer to your
   host to VNC screens :1 thru :5 (ports 5901-5905):

   ::

       sudo ./start-vm.sh 5

8. Turn VMs off. You may simply kill all KVM processes by

   ::

       sudo killall kvm

Baseline Data
=============

The table below provides baseline data which we've got in our
environment.

**Avg. Time** refers to the lab with recommended hardware configuration,
while **Max. Time** refers to minimal hardware configuration.

+--------------------------+--------------------------+---------------------+
|                          | Boot ONE instance        | Boot FIVE instances |
+==========================+==========================+=====================+
| Avg. Time                | 3m:40s                   | 8m                  |
+--------------------------+--------------------------+---------------------+
| Max. Time                | 5m                       | 20m                 |
+--------------------------+--------------------------+---------------------+

Host Optimizations
==================

Default KVM installation could be improved to provide better
performance.

The following optimizations may improve host performance up to 30%:

* change default scheduler from **CFQ** to **Deadline**
* use **ksm**
* use **vhost-net**
