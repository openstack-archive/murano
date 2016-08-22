=============
Configure SSL
=============

Murano components can work with SSL. This section provides information on
how to set SSL properly.

Configure SSL for Murano API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To configure SSL for the Murano API service, modify the ``[ssl]`` section in ``/etc/murano/murano.conf``:

.. code-block:: ini

   [ssl]
   cert_file = <PATH>
   key_file = <PATH>
   ca_file = <PATH>

.. list-table::
   :widths: 10 25
   :header-rows: 1

   * - Parameter
     - Description
   * - ``cert_file``
     - A path to the certificate file the server should use when binding to an SSL-wrapped socket.
   * - ``key_file``
     - A path to the private key file the server should use when binding to an SSL-wrapped socket.
   * - ``ca_file``
     - A path to the CA certificate file the server should use to validate client certificates provided during an SSL handshake. This parameter is ignored if the ``cert_file`` and ``key_file`` parameters are not set.

Murano API starts using SSL automatically after you point to the HTTPS protocol
instead of HTTP during the registration of the Murano API service
in endpoints, modifying the ``publicurl`` argument to start with ``https://``.

SSL for Murano API is implemented the same way as in any other OpenStack
component. See `ssl python module
<https://docs.python.org/2/library/ssl.html>`_ for details.

Configure SSL for RabbitMQ
~~~~~~~~~~~~~~~~~~~~~~~~~~

All murano components communicate with each other using RabbitMQ.
By default, all messages in RabbitMQ are not encrypted. You can encrypt
this interaction with SSL. Configure each RabbitMQ exchange separately.

Murano API <-> RabbitMQ <-> Murano engine
-----------------------------------------

Modify the ``[default]`` section in the ``/etc/murano/murano.conf`` file:

#. Enable SSL for RabbitMQ:

   .. code-block:: ini

      # connect over SSL for RabbitMQ (boolean value)
      rabbit_use_ssl = true


#. Set the ``kombu`` parameters.

   Specify the paths to the SSL key file and SSL CA certificate in a regular
   ``</PATH/TO/FILE>`` format without quotes or leave them empty to enable
   self-signed certificates:

   .. code-block:: ini

      # SSL version to use (valid only if SSL enabled). valid values
      # are TLSv1, SSLv23 and SSLv3. SSLv2 may be available on some
      # distributions (string value)
      kombu_ssl_version =

      # SSL key file (valid only if SSL enabled) (string value)
      kombu_ssl_keyfile =

      # SSL cert file (valid only if SSL enabled) (string value)
      kombu_ssl_certfile =

      # SSL certification authority file (valid only if SSL enabled)
      # (string value)
      kombu_ssl_ca_certs =

Murano agent -> RabbitMQ
------------------------

To encrypt the communication between the murano agent and RabbitMQ,
set ``ssl = True`` in the  ``[rabbitmq]`` section of
``/etc/murano/murano.conf``:

.. code-block:: ini

   [rabbitmq]
   ...
   ssl = True
   insecure = False

If you want to configure the murano agent differently, you need to change
the `default template <http://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Resources/Agent-v1.template>`_ located in the murano core library.
After you finish with the template modification, verify that you zip and
re-upload the murano core library.

Configure SSL for the Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not plan to use self-signed certificates, no additional
configurations are required. Just point your web browser to the URL
starting with ``https://``.

Otherwise, set the ``MURANO_API_INSECURE`` parameter to ``True`` in
``/etc/openstack-dashboard/local_settings.py``.
