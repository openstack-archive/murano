===================
System requirements
===================

This section provides basic information about the murano environment system
requirements. Additionally, it contains a description of the performance
test scenario, which you may use to check if your hardware fits
the requirements. To do this, run the test and compare the results with
the baseline data provided.

Software prerequisites
~~~~~~~~~~~~~~~~~~~~~~

Before you install murano, verify your system meets the following
prerequisites.

**Supported operating systems:**

* Ubuntu Server 14.04 LTS
* RHEL/CentOS
* Debian

**System packages for Ubuntu:**

* gcc
* python-pip
* python-dev
* libxml2-dev
* libxslt-dev
* libffi-dev
* libpq-dev
* python-openssl
* mysql-client

**System packages for CentOS:**

* gcc
* python-pip
* python-devel
* libxml2-devel
* libxslt-devel
* libffi-devel
* postgresql-devel
* pyOpenSSL
* mysql

Hardware requirements
~~~~~~~~~~~~~~~~~~~~~

We recommend that your system meets the following hardware requirements:

+------------+--------------------------------+----------------------+
| Criteria   | Minimal                        | Recommended          |
+============+================================+======================+
| CPU        | 4 core @ 2.4 GHz               | 24 core @ 2.67 GHz   |
+------------+--------------------------------+----------------------+
| RAM        | 8 GB                           | 24 GB or more        |
+------------+--------------------------------+----------------------+
| HDD        | 2 x 500 GB (7200 rpm)          | 4 x 500 GB (7200 rpm)|
+------------+--------------------------------+----------------------+
| RAID       | Software RAID-1 (use mdadm as  | Hardware RAID-10     |
|            | it improves the read           |                      |
|            | performance almost twice)      |                      |
+------------+--------------------------------+----------------------+

Other possible storage configurations:

* 1x SSD 500+ GB

* 1x HDD (7200 rpm) 500+ GB and 1x SSD 250+ GB (install the system onto
  the HDD and mount the SSD drive to the directory where the virtual
  machines images are stored)

* 1x HDD (15000 rpm) 500+ GB

Testing the performance
~~~~~~~~~~~~~~~~~~~~~~~

We have measured the time required to boot 1 to 5 instances of the Windows
operating system simultaneously. You can use this data as the baseline
to check if your system is fast enough.

.. note::

   Use *sysprepped* images for this test to simulate an instance first boot.

To reproduce the performance test, proceed with the following steps:

#. Prepare a Windows 2012 Standard (with GUI) image in the ``QCOW2`` format.
   This example uses the ``ws-2012-std.qcow2`` image.

#. Verify that there are no KVM processes running on the host:

   .. code-block:: console

      ps aux | grep kvm

#. Make 5 copies of the Windows image file:

   .. code-block:: console

      for i in $(seq 5); do \
      cp ws-2012-std.qcow2 ws-2012-std-$i.qcow2; done

#. Create the ``start-vm.sh`` script in the directory with the ``.qcow2``
   files:

   .. code-block:: console

      #!/bin/bash
      [ -z $1 ] || echo "VM count not provided!"; exit 1
      for i in $(seq $1); do
      echo "Starting VM $i ..."
      kvm -m 1024 -drive file=ws-2012-std-$i.qcow2,if=virtio -net user -net nic,model=virtio -nographic -usbdevice tablet -vnc :$i & done

#. Start ONE instance using the command below (as root) and measure time
   between the instance launch and the moment when the Server Manager window
   displays.

   .. code-block:: console

      sudo ./start-vm.sh 1

   To view the instance desktop, connect with VNC viewer to your host
   to VNC screen :1 (port 5901).

#. Turn off the instance. You may simply kill all KVM processes by running:

   .. code-block:: console

      sudo killall kvm

#. Start FIVE instances with the command below (as root) and measure time
   interval between ALL instances launch and the moment when the LAST
   Server Manager window displays.

   .. code-block:: console

      sudo ./start-vm.sh 5

   To view VM's desktops, connect with VNC viewer to your
   host to VNC screens :1 thru :5 (ports 5901-5905).

#. Turn off the instances. You may simply kill all KVM processes by running:

   .. code-block:: console

      sudo killall kvm

Baseline data
-------------

The table below provides the baseline data that was received in our test
murano environment.

+--------------------------+--------------------------+---------------------+
|                          | Boot ONE instance        | Boot FIVE instances |
+==========================+==========================+=====================+
| Avg. Time                | 3m:40s                   | 8m                  |
+--------------------------+--------------------------+---------------------+
| Max. Time                | 5m                       | 20m                 |
+--------------------------+--------------------------+---------------------+

**Avg. Time**
 Refers to the environment with the recommended hardware configuration

**Max. Time**
 Refers to the minimal hardware configuration

Host optimizations
------------------

You can improve your default KVM installation performance with the following
optimizations up to 30%:

* Change the default scheduler from **CFQ** to **Deadline**
* Use **ksm**
* Use **vhost-net**
