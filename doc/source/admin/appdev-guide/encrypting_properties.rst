.. _encrypting-properties:

=================================
Managing Sensitive Data in Murano
=================================

Overview
--------
If you are developing a Murano application that manages sensitive data such as
passwords, user data, etc, you may want to ensure this is stored in a secure
manner in the Murano backend.

Murano offers two `yaql` functions to do this, `encryptData` and
`decryptData`.

.. note:: Barbican or a similar compatible secret storage backend must be
          configured to use this feature.

Configuring
-----------
Murano makes use of Castellan_ to manage encryption using a supported secret
storage backend. As of OpenStack Pike, Barbican_ is the only supported
backend, and hence is the one tested by the Murano community.

To configure Murano to use Barbican, place the following configuration into
`murano-engine.conf`::

  [key_manager]
  auth_type = keystone_password
  auth_url = <keystone_url>
  username = <username>
  password = <password>
  user_domain_name = <domain_name>

Similarly, place the following configuration into `_50_murano.py` to configure
the murano-dashboard end::

    KEY_MANAGER = {
            'auth_url': '<keystone_url>/v3',
            'username': '<username>',
            'user_domain_name': '<domain_name>',
            'password': '<password>',
            'project_name': '<project_name>',
            'project_domain_name': '<domain_name>'
    }

.. note:: Horizon config must be valid Python, so the quotes above are important.

Example
-------
`encryptData(foo)`: Call to encrypt string `foo` in storage. Will return a
`uuid` which is used to retrieve the encrypted value.

`decryptData(foo_key)`: Call to decrypt and retrieve the value represented by
`foo_key` from storage.

There is an example application available in the murano repository_.

.. _Castellan: https://github.com/openstack/castellan
.. _Barbican: https://github.com/openstack/barbican
.. _repository: https://git.openstack.org/cgit/openstack/murano/tree/contrib/packages/EncryptionDemo
