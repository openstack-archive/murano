Prerequisites
-------------

Before you install and configure the Application Catalog service,
you must create a database, service credentials, and API endpoints.

#. To create the database, complete these steps:

   Murano can use various database types on the back end. For development
   purposes, SQLite is enough in most cases. For production installations, you
   should use MySQL or PostgreSQL databases.

   .. warning::

      Although murano could use a PostgreSQL database on the back end,
      it wasn't thoroughly tested and should be used with caution.
   ..


   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p
     ..

   * Create the ``murano`` database:

     .. code-block:: mysql

            CREATE DATABASE murano;
     ..

   * Grant proper access to the ``murano`` database:

     .. code-block:: mysql

            GRANT ALL PRIVILEGES ON murano.* TO 'murano'@'localhost' IDENTIFIED BY 'MURANO_DBPASS';
     ..

     Replace ``MURANO_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: mysql

            exit;
     ..

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc
   ..

#. To create the service credentials, complete these steps:

   * Create the ``murano`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt murano
     ..

   * Add the ``admin`` role to the ``murano`` user:

     .. code-block:: console

        $ openstack role add --project service --user murano admin
     ..

   * Create the murano service entities:

     .. code-block:: console

        $ openstack service create --name murano --description "Application Catalog" application-catalog
     ..

#. Create the Application Catalog service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        application-catalog public http://<murano-ip>:8082
      $ openstack endpoint create --region RegionOne \
        application-catalog internal http://<murano-ip>:8082
      $ openstack endpoint create --region RegionOne \
        application-catalog admin http://<murano-ip>:8082
   ..

   .. note::

      URLs (publicurl, internalurl and adminurl) may be different
      depending on your environment.
   ..
