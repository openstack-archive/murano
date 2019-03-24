===========
Linux Image
===========

At the moment the best way to build a Linux image with the murano agent is
to use disk image builder.


.. note::

    Disk image builder requires sudo rights


The process is quite simple. Let's assume that you use a directory ~/git
for cloning git repositories:

.. code-block:: console

    export GITDIR=~/git
    mkdir -p $GITDIR


Clone the components required to build an image to that directory:

.. code-block:: console

    cd $GITDIR
    git clone https://git.openstack.org/openstack/murano
    git clone https://git.openstack.org/openstack/murano-agent


Install diskimage-builder

.. code-block:: console

    sudo pip install diskimage-builder


Install additional packages required by disk image builder:

.. code-block:: console

    sudo apt-get install qemu-utils curl python-tox


Export paths where additional dib elements are located:

.. code-block:: console

    export ELEMENTS_PATH=$GITDIR/murano/contrib/elements:$GITDIR/murano-agent/contrib/elements


Build Ubuntu-based image with the murano agent:

.. code-block:: console

    disk-image-create vm ubuntu murano-agent -o murano-agent.qcow2


If you need a Fedora based image, replace 'ubuntu' to 'fedora' in the last command.

It'll take a while (up to 30 minutes if your hard drive and internet connection are slow).

When you are done upload the murano-agent.qcow2 image to glance and play :)
