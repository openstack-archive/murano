Murano Plugin for Cloudify
~~~~~~~~~~~~~~~~~~~~~~~~~~

Cloudify is a TOSCA-based open-source cloud orchestration engine by GigaSpaces
Technologies.

This plugin extends Murano with support of Cloudify TOSCA package format.
TOSCA packages can be deployed on Cloudify Manager deployed at configurable
location.

Plugin registers `Cloudify.TOSCA/1.0` format identifier.

Installation
------------

Installation of the plugin is done using any of Python package management
tools. The most simple way is by saying `pip install .` from the plugin's
directory (or `pip install -e .` for development)

Also location of Cloudify Manager (engine server) must be configured
in murano config file. This is done in `[cloudify]` section of murano.conf
via cloudify_manager setting. For example:

.. code-block:: ini

    [cloudify]
    cloudify_manager = 10.10.1.10


Murano engine must be restarted after installation of the plugin.


Requirements
------------

All Cloudify TOSCA application require `org.getcloudify.murano` library package
to be present in Murano catalog. The package can be found in
`cloudify_applications_library` subfolder.


Demo application
----------------

There is a demo application that can be used to test the plugin.
It is located in `nodecellar_example_application` subfolder. Follow
instructions at `nodecellar_example_application/README.rst` to build
the demo package.


