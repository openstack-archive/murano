.. _install:

Install and configure
~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the
Application Catalog service, code-named murano, on the controller node.

This section assumes that you already have a working OpenStack environment with
at least the following components installed: Identity service, Image service,
Compute service, Networking service, Block Storage service and Orchestration
service. See `OpenStack Install Guides <https://docs.openstack.org/
#install-guides>`__.

Note that installation and configuration vary by distribution. Currently,
this installation guide is tailored toward Ubuntu environments, but can easily
be adapted to work with other types of distros.

.. note::

    Fedora support wasn't thoroughly tested. We do not guarantee that murano
    will work on Fedora.
..

.. toctree::
   :maxdepth: 2

   install-api.rst
   install-dashboard.rst
   from-source.rst
   install-network-config.rst
   enable-ssl.rst
