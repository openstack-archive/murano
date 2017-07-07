.. _multi-region:

=============================
Support for OpenStack regions
=============================
Murano supports multi-region deployment. If OpenStack setup has several regions
it is possible to choose the region to deploy an application.

There is the new option in the murano configuration file:

*  `home_region` - default region name used to get services
   endpoints. The region where murano-api resides.

Now murano has two possible ways to deploy apps in different regions:

1. Deploy an application in the current murano region.
2. Associate environments with regions.

Deploy an app in the current region
===================================
Each region has a copy of murano services and its own RabbitMQ for api to
engine communication. In this case application will be deployed to the same
region that murano run in.

.. seealso::

    :ref:`multi_region`

Associate environments with regions
===================================
Murano services are in one region but environments can be associated with
different regions. There are two new properties in the class
`io.murano.Environment`:

*  `regionConfigs` - a dict with RabbitMQ settings for each region. The
   structure of the agentRabbitMq part of the dict is identical to [rabbitmq]
   section in the `murano.conf` file. For example:

   .. code-block:: yaml

       regionConfigs:
         RegionOne:
           agentRabbitMq:
             host: 192.1.1.1
             login: admin
             password: admin

   User can store such configs as YAML or JSON files. These config files must
   be stored in a special folder that is configured in [engine] section of
   `murano.conf` file under `class_configs` key and must be named using
   %FQ class name%.json or %FQ class name%.yaml pattern.

*  `region` - region name to deploy an app. It can be passed when creating
   environment via CLI:

   .. code-block:: console

       murano environment-create environment_name --region RegionOne

   If it is not specified a value from `home_region` option of `murano.conf`
   file will be used.
