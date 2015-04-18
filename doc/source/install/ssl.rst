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

=================
SSL configuration
=================
Murano components are able to work with SSL. This chapter will help your
to make proper settings with SSL configuration.

HTTPS for Murano API
====================

SSL for Murano API service can be configured in *ssl* section in
``/etc/murano/murano.conf``. Just point to a valid SSL certificate.
See the example below:

::


    [ssl]
    cert_file = PATH
    key_file = PATH
    ca_file = PATH

- *cert\_file*    Path to the certificate file the server should use when binding to an SSL-wrapped socket.
- *key\_file*     Path to the private key file the server should use when binding to an SSL-wrapped socket.
- *ca\_file*      Path to the CA certificate file the server should use to validate client certificates provided during an SSL handshake. This is ignored if cert\_file and "key\_file" are not set.

The use of SSL is automatically started after point to HTTPS protocol
instead of HTTP during registration Murano API service in endpoints
(Change publicurl argument to start with \https://).
SSL for Murano API is implemented like in any other Openstack component.
This realization is based on ssl python module so more information about
it can be found `here`_.

.. _`here`: https://docs.python.org/2/library/ssl.html

SSL for RabbitMQ
================

All Murano components communicate with each other by RabbitMQ. This
interaction can be encrypted with SSL. By default all messages in Rabbit
MQ are not encrypted. Each RabbitMQ Exchange should be configured
separately.

**Murano API <-> Rabbit MQ exchange <-> Murano Engine**

Edit ssl parameters in default section of ``/etc/murano/murano.conf``. Set ``rabbit_use_ssl`` option to *true* and configure ssl kombu parameters.
Specify the path to the SSL keyfile and SSL CA certificate in a regular format: /path/to/file without quotes or leave it empty to
allow self-signed certificates.

::

   # connect over SSL for RabbitMQ (boolean value)
   #rabbit_use_ssl=false

   # SSL version to use (valid only if SSL enabled). valid values
   # are TLSv1, SSLv23 and SSLv3. SSLv2 may be available on some
   # distributions (string value)
   #kombu_ssl_version=

   # SSL key file (valid only if SSL enabled) (string value)
   #kombu_ssl_keyfile=

   # SSL cert file (valid only if SSL enabled) (string value)
   #kombu_ssl_certfile=

   # SSL certification authority file (valid only if SSL enabled)
   # (string value)
   #kombu_ssl_ca_certs=


**Murano Agent -> Rabbit MQ exchange**

In main murano configuration file there is a section ,named *rabbitmq*, that is responsible for set up communication between Murano Agent and Rabbit MQ.
Just set *ssl* parameter to True to enable ssl.

::

    [rabbitmq]
    host = localhost
    port = 5672
    login = guest
    password = guest
    virtual_host = /
    ssl = True

If you want to configure Murano Agent in a different way change
the default template. It can be found in Murano Core Library, located at *http://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/Resources/Agent-v1.template*. Take
a look at appSettings section:

::

    <appSettings>
            <add key="rabbitmq.host" value="%RABBITMQ_HOST%"/>
            <add key="rabbitmq.port" value="%RABBITMQ_PORT%"/>
            <add key="rabbitmq.user" value="%RABBITMQ_USER%"/>
            <add key="rabbitmq.password" value="%RABBITMQ_PASSWORD%"/>
            <add key="rabbitmq.vhost" value="%RABBITMQ_VHOST%"/>
            <add key="rabbitmq.inputQueue" value="%RABBITMQ_INPUT_QUEUE%"/>
            <add key="rabbitmq.resultExchange" value=""/>
            <add key="rabbitmq.resultRoutingKey" value="%RESULT_QUEUE%"/>
            <add key="rabbitmq.durableMessages" value="true"/>

            <add key="rabbitmq.ssl" value="%RABBITMQ_SSL%"/>
            <add key="rabbitmq.allowInvalidCA" value="true"/>
            <add key="rabbitmq.sslServerName" value=""/>

        </appSettings>


Desired parameter should be set directly to the value of the key that
you want to change. Quotes are need to be kept. Thus you can change
"rabbitmq.ssl" and "rabbitmq.port" values to make Rabbit MQ work with
this exchange in a different from Murano-Engine way.
After modification, don't forget to zip and re-upload core library.

SSL for Murano Dashboard
========================

If you are going not to use self-signed certificates additional
configuration do not need to be done. Just point https in the URL.
Otherwise, set *MURANO_API_INSECURE = True* on horizon config. You can
find it in ``/etc/openstack-dashboard/local_settings.py.``.
