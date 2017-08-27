.. _glare_usage:

=====================================
Using Glare as a storage for packages
=====================================

DevStack installation
---------------------

#. Enable Glare service in DevStack

   To enable the Glare service in DevStack, edit the ``local.conf`` file:

   .. code-block:: console

      $ cat local.conf
      [[local|localrc]]
      enable_service g-glare

#. Run DevStack:

   .. code-block:: console

      $ ./stack.sh

   **Result** Glare service is installed with DevStack.
   You can find logs in ``g-glare`` screen session.

#. Install the ``muranoartifact`` plug-in from ``murano/contrib``

   .. code-block:: console

      $ cd $DEST/murano/contrib/glance/
      $ sudo pip install -e .

#. Restart ``Glare``

#. Set Glare as packages service in murano-engine. For this,
   edit the ``[engine]`` section in the ``murano.conf`` file.
   By default, ``murano.conf`` is located in the ``/etc/murano`` directory

   .. code-block:: ini

      [engine]

      packages_service = glare

#. Restart ``murano-engine``

   .. note:: You also can use ``glance`` as a value of the
             ``packages_service`` option for the same behaviour

#. Enable Glare in ``murano-dashboard``. For this, modify the following line
   in the ``_50_murano.py`` file

   .. code-block:: python

      MURANO_USE_GLARE = True

   By default, the ``_50_murano.py`` file is located in
   ``$HORIZON_DIR/openstack_dashboard/local/local_settings.d/``.

#. Restart the ``apache2`` service.
   Now ``murano-dashboard`` will retrieve packages from Glare.

#. Log in to Dashboard and navigate to :menuselection:`Applications > Manage > Packages`
   to view the empty list of packages.
   Alternatively, use the :command:`murano` command.

#. Use ``--murano-packages-service`` option to specify backend,
   used by :command:`murano` command. Set it to ``glare`` for using ``Glare``

   .. note:: You also can use ``glance`` as value
             of ``--murano-packages-service`` option or environment variable
             ``MURANO_PACKAGES_SERVICE`` for same behaviour

   + View list of packages:

     .. code-block:: console

         $ . {DEVSTACK_SOURCE_DIR}/openrc admin admin
         $ murano --murano-packages-service=glare  package-list

         +----+------+-----+--------+--------+-----------+------+---------+
         | ID | Name | FQN | Author | Active | Is Public | Type | Version |
         +----+------+-----+--------+--------+-----------+------+---------+
         +----+------+-----+--------+--------+-----------+------+---------+

   + Importing ``Core library``

     .. code-block:: console

         $ cd $DEST/murano/meta/io.murano/
         $ zip io.murano.zip -r *
         $ murano --murano-packages-service=glare  package-import \
             --is-public /opt/stack/murano/meta/io.murano/io.murano.zip

         Importing package io.murano
         +--------------------------------------+--------------+-----------+-----------+--------+-----------+---------+---------+
         | ID                                   | Name         | FQN       | Author    | Active | Is Public | Type    | Version |
         +--------------------------------------+--------------+-----------+-----------+--------+-----------+---------+---------+
         | 91a9c78f-f23a-4c82-aeda-14c8cbef096a | Core library | io.murano | murano.io | True   |           | Library | 0.0.0   |
         +--------------------------------------+--------------+-----------+-----------+--------+-----------+---------+---------+

Set up Glare API entrypoint manually
------------------------------------

If you do not plan to get Glare service from keystone application catalog,
specify where g-glare service is running.

#. Specify Glare URL in ``murano.conf``.It is http://0.0.0.0:9494 by default
   and can be changed by setting `bind_host` and `bind_port` options in
   the ``glance-glare.conf`` file.

   .. code-block:: ini

      [glare]

      url = http://<GLARE_API_URL>:<GLARE_API_PORT>

#. Specify Glare URL in the Dashboard settings file, ``_50_murano.py`` :

   .. code-block:: python

      GLARE_API_URL = 'http://<GLARE_API>:<GLARE_API_PORT>'

#. Set the ``GLARE_URL`` environment variable for python-muranoclient.
   Alternatively, use the ``--glare-url`` option in CLI.

   .. code-block:: console

      $ murano --murano-packages-service=glare --glare-url=http://0.0.0.0:9494  package-list
