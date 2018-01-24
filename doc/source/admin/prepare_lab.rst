========================
Prepare a lab for murano
========================
This section provides basic information about lab's system requirements.
It also contains a description of a test which you may use to check if
your hardware fits the requirements. To do this, run the test and
compare the results with baseline data provided.

.. _system_prerequisites:

System prerequisites
~~~~~~~~~~~~~~~~~~~~

Supported operating systems
---------------------------

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

Install all the requirements on Ubuntu by running::

  sudo apt-get install gcc python-pip python-dev \
  libxml2-dev libxslt-dev libffi-dev \
  libpq-dev python-openssl mysql-client

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

Install all the requirements on CentOS by running::

  sudo yum install gcc python-pip python-devel libxml2-devel \
  libxslt-devel libffi-devel postgresql-devel pyOpenSSL \
  mysql

.. _lab_requirements:

Lab requirements
----------------

+------------+--------------------------------+-----------------------+
| Criteria   | Minimal                        | Recommended           |
+============+================================+=======================+
| CPU        | 4 core @ 2.4 GHz               | 24 core @ 2.67 GHz    |
+------------+--------------------------------+-----------------------+
| RAM        | 8 GB                           | 24 GB or more         |
+------------+--------------------------------+-----------------------+
| HDD        | 2 x 500 GB (7200 rpm)          | 4 x 500 GB (7200 rpm) |
+------------+--------------------------------+-----------------------+
| RAID       | Software RAID-1 (use mdadm as  | Hardware RAID-10      |
|            | it will improve read           |                       |
|            | performance almost two times)  |                       |
+------------+--------------------------------+-----------------------+

`Table: Hardware requirements`

There are a few possible storage configurations except the shown above.
All of them were tested and were working well.

* 1x SSD 500+ GB

* 1x HDD (7200 rpm) 500+ GB and 1x SSD 250+ GB (install the system onto
   the HDD and mount the SSD drive to folder where VM images are)

* 1x HDD (15000 rpm) 500+ GB


Test your lab host performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have measured time required to boot 1 to 5 instances of Windows
system simultaneously. You can use this data as the baseline to check if
your system is fast enough.

You should use sysprepped images for this test, to simulate VM first
boot.

Steps to reproduce test:

#. Prepare Windows 2012 Standard (with GUI) image in QCOW2 format. Let's
   assume that its name is ws-2012-std.qcow2

#. Ensure that there is NO KVM PROCESSES on the host. To do this, run
   command:

   .. code-block:: console

       ps aux | grep kvm

#. Make 5 copies of Windows image file:

   .. code-block:: console

       for i in $(seq 5); do \
       cp ws-2012-std.qcow2 ws-2012-std-$i.qcow2; done

#. Create script start-vm.sh in the folder with .qcow2 files:

   .. code-block:: console

       #!/bin/bash
       [ -z $1 ] || echo "VM count not provided!"; exit 1
       for i in $(seq $1); do
       echo "Starting VM $i ..."
       kvm -m 1024 -drive file=ws-2012-std-$i.qcow2,if=virtio -net user -net nic,model=virtio -nographic -usbdevice tablet -vnc :$i & done

#. Start ONE instance with command below (as root) and measure time
   between VM's launch and the moment when Server Manager window
   appears. To view VM's desktop, connect with VNC viewer to your host
   to VNC screen :1 (port 5901):

   .. code-block:: console

       sudo ./start-vm.sh 1

#. Turn VM off. You may simply kill all KVM processes by

   .. code-block:: console

       sudo killall kvm

#. Start FIVE instances with command below (as root) and measure time
   interval between ALL VM's launch and the moment when LAST Server Manager
   window appears. To view VM's desktops, connect with VNC viewer to your
   host to VNC screens :1 thru :5 (ports 5901-5905):

   .. code-block:: console

       sudo ./start-vm.sh 5

#. Turn VMs off. You may simply kill all KVM processes by

   .. code-block:: console

       sudo killall kvm


Baseline data
~~~~~~~~~~~~~

The table below provides baseline data which we've got in our
environment.

+----------------+--------------------------+---------------------+
|                | Boot 1 instance          | Boot 5  instances   |
+================+==========================+=====================+
| Avg. Time      | 3m:40s                   | 8m                  |
+----------------+--------------------------+---------------------+
| Max. Time      | 5m                       | 20m                 |
+----------------+--------------------------+---------------------+

``Avg. Time`` refers to the lab with recommended hardware configuration,
while ``Max. Time`` refers to minimal hardware configuration.


Host optimizations
~~~~~~~~~~~~~~~~~~

Default KVM installation could be improved to provide better
performance.

The following optimizations may improve host performance up to 30%:

* change default scheduler from ``CFQ`` to ``Deadline``
* use ``ksm``
* use ``vhost-net``
