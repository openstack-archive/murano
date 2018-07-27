Installing Murano API via WSGI
==============================

This document is a guide to deploy murano using two WSGI mode uwsgi and
mod_wsgi of Apache.

Please note that if you intend to use mode uwsgi, you should install
``mode_proxy_uwsgi`` module. For example on deb-base system:

.. code-block:: console

    # sudo apt-get install libapache2-mod-proxy-uwsgi
    # sudo a2enmod proxy
    # sudo a2enmod proxy_uwsgi

.. end

WSGI Application
----------------

The function ``murano.httpd.init_application`` will setup a WSGI application
to run behind uwsgi and mod_wsgi

Murano API behind uwsgi
-----------------------

Create a ``murano-api-uwsgi`` file with content below:

.. code-block:: ini

    [uwsgi]
    chmod-socket = 666
    socket = /var/run/uwsgi/murano-wsgi-api.socket
    lazy-apps = true
    add-header = Connection: close
    buffer-size = 65535
    hook-master-start = unix_signal:15 gracefully_kill_them_all
    thunder-lock = true
    plugins = python
    enable-threads = true
    worker-reload-mercy = 90
    exit-on-reload = false
    die-on-term = true
    master = true
    processes = 2
    wsgi-file = <path-to-murano-bin-dir>/murano-wsgi-api

.. end

Start murano-api:

.. code-block:: console

    # uwsgi --ini /etc/murano/murano-api-uwsgi.ini

.. end

Murano API behind mod_wsgi
--------------------------

Create ``/etc/apache2/murano.conf`` with content below:

.. code-block:: ini

    Listen 8082

    <VirtualHost *:8082>
        WSGIDaemonProcess murano-api processes=1 threads=10 user=%USER% display-name=%{GROUP} %VIRTUALENV%
        WSGIProcessGroup murano-api
        WSGIScriptAlias / %MURANO_BIN_DIR%/murano-wsgi-api
        WSGIApplicationGroup %{GLOBAL}
        WSGIPassAuthorization On
        AllowEncodedSlashes On
        <IfVersion >= 2.4>
          ErrorLogFormat "%{cu}t %M"
        </IfVersion>
        ErrorLog /var/log/%APACHE_NAME%/murano_api.log
        CustomLog /var/log/%APACHE_NAME%/murano_api_access.log combined

        <Directory %MURANO_BIN_DIR%>
            <IfVersion >= 2.4>
                Require all granted
            </IfVersion>
            <IfVersion < 2.4>
                Order allow,deny
                Allow from all
            </IfVersion>
        </Directory>
    </VirtualHost>

.. end

Then on deb-based systems copy or symlink the file to ``/etc/apache2/sites-available``.
For rpm-based systems the file will go in ``/etc/httpd/conf.d``.

Enable the murano site. On deb-based systems:

.. code-block:: console

    # a2ensite murano
    # systemctl reload apache2.service

.. end

On rpm-based systems:

.. code-block:: console

    # systemctl reload httpd.service

.. end

