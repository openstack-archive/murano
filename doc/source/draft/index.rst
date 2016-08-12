.. meta::
   :robots: noindex, nofollow

.. _content:

======================================
Welcome to Murano Documentation (BETA)
======================================

**Murano** is an open source OpenStack project that
combines an application catalog with versatile
tooling to simplify and accelerate packaging and
deployment. It can be used with almost any application
and service in OpenStack.

This documentation guides application developers
through the process of composing an application
package to get it ready for uploading to Murano.

Besides the deployment rules and requirements,
it contains information on how to manage images,
categories, and repositories using the murano client that
will surely be helpful for cloud administrators.

It also explains to end users how they can use the catalog
directly from the dashboard. These include guidance on how
to manage applications and environments.

And of course, it provides information on how to contribute
to the project.

Deploying Murano
~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   admin-guide/deploy_murano
   admin-guide/prepare_lab
   admin-guide/configuration
   admin-guide/manage_packages
   admin-guide/manage_images
   admin-guide/manage_categories
   admin-guide/murano_repository
   admin-guide/murano_agent
   admin-guide/policy_enf
   admin-guide/configure_cloud_foundry_service_broker
   admin-guide/using_glare.rst
   admin-guide/admin_troubleshooting

Contributing
~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   contributor-guide/how_to_contribute
   contributor-guide/dev_guidelines
   contributor-guide/plugins
   contributor-guide/dev_env
   contributor-guide/testing
   contributor-guide/doc_guidelines
   contributor-guide/stable_branches

Appendix
~~~~~~~~

.. toctree::
   :maxdepth: 2

   appendix/glossary
   appendix/murano_concepts
   appendix/tutorials
   appendix/rest_api_spec
   appendix/cli_ref
