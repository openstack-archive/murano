.. _hot-packages:

============
HOT packages
============

.. include:: hotpackages/compose.rst

Hot packages with nested Heat templates
---------------------------------------

In Murano HOT packages it is possible to allow Heat nested templates to be
saved and deployed as part of a Murano Heat applications. Such templates
should be placed in package under ‘/Resources/HotFiles’. Adding additional
templates to a package is optional. When a Heat generated package is being
deployed, if there are any Heat nested templates located in the package under
‘/Resources/HotFiles’, they are sent to Heat together with the main template
and params during stack creation.

These nested templates can be referenced by putting the template name into the
``type`` attribute of resource definition, in the main template. This
mechanism then compose one logical stack with these multiple templates. The
following examples illustrate how you can use a custom template to define new
types of resources. These examples use a custom template stored in a
``sub_template.yaml`` file

 .. code-block:: yaml

     heat_template_version: 2015-04-30

     parameters:
       key_name:
           type: string
           description: Name of a KeyPair

     resources:
       server:
         type: OS::Nova::Server
         properties:
           key_name: {get_param: key_name}
           flavor: m1.small
           image: ubuntu-trusty

Use the template filename as type
---------------------------------

The following main template defines the ``sub_template.yaml`` file as value for
the type property of a resource

  .. code-block:: yaml

      heat_template_version: 2015-04-30

      resources:
        my_server:
          type: sub_template.yaml
          properties:
            key_name: my_key

.. note::
    This feature is supported Liberty onwards.