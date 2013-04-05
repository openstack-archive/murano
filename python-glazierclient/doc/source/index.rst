Glazier API Client
==================
In order to use the python api directly, you must first obtain an auth token and identify which endpoint you wish to speak to. Once you have done so, you can use the API like so::

    >>> from glazierclient import Client
    >>> glazier = Client('1', endpoint=GLAZIER_URL, token=OS_AUTH_TOKEN)
...


Command-line Tool
=================
In order to use the CLI, you must provide your OpenStack username, password, tenant, and auth endpoint. Use the corresponding configuration options (``--os-username``, ``--os-password``, ``--os-tenant-id``, and ``--os-auth-url``) or set them in environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_TENANT_ID=b363706f891f48019483f8bd6503c54b
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0

The command line tool will attempt to reauthenticate using your provided credentials for every request. You can override this behavior by manually supplying an auth token using ``--os-image-url`` and ``--os-auth-token``. You can alternatively set these environment variables::

    export GLAZIER_URL=http://glazier.example.org:8082/
    export OS_AUTH_TOKEN=3bcc3d3a03f44e3d8377f9247b0ad155

Once you've configured your authentication parameters, you can run ``glazier help`` to see a complete listing of available commands.


Release Notes
=============

0.1.0
-----
* Initial release
