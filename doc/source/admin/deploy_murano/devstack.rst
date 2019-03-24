==============================
Integrate murano with DevStack
==============================

You can install murano with DevStack. The `murano/devstack`_ directory
in the murano repository contains the files necessary to integrate murano
with `DevStack`_.

To install the development version of an OpenStack environment
with murano, proceed with the following steps:

#. Download DevStack:

   .. code-block:: console

      git clone https://git.openstack.org/openstack-dev/devstack
      cd devstack

#. Edit ``local.conf`` to enable murano DevStack plug-in:

   .. code-block:: console

      > cat local.conf
      [[local|localrc]]
      enable_plugin murano https://git.openstack.org/openstack/murano

#. If you want to enable Murano Cloud Foundry Broker API service, add the
   following line to ``local.conf``:

   .. code-block:: ini

      enable_service murano-cfapi

#. If you want to use Glare Artifact Repository as a strorage for packages,
   add the following line to ``local.conf``:

   .. code-block:: ini

      enable_service g-glare

   For more information on how to use Glare Artifact Repository,
   see :ref:`glare_usage`.

#. (Optional) To import murano packages when DevStack is up, define an ordered
   list of FQDN packages in ``local.conf``. Verify that you list all package
   dependencies. These packages will be imported from the ``murano-apps``
   git repository by default. For example:

   .. code-block:: ini

      MURANO_APPS=com.example.apache.Tomcat,com.example.Guacamole

   To configure the git repository that will be used as the source for
   the imported packages, configure the ``MURANO_APPS_REPO`` and
   ``MURANO_APPS_BRANCH`` variables.

#. Run DevStack:

   .. code-block:: console

    ./stack.sh

**Result:** Murano has installed with DevStack.

.. Links
.. _DevStack: https://docs.openstack.org/devstack/latest/
.. _murano/devstack: https://git.openstack.org/cgit/openstack/murano/tree/devstack
