Glazier Manuals
+++++++++++++++++

This repository contains documentation for the
Glazier project. It includes:

 * API Specification
 * Architecture

For more details, see the `Glazier <http://glazier.mirantis.com>`_.

Prerequisites
=============
`Apache Maven <http://maven.apache.org/>`_ must be installed to build the
documentation.

To install Maven 3 for Ubuntu 12.04 and later,and Debian wheezy and later::

    apt-get install maven

On Fedora 15 and later::

    yum install maven3

Building
========
The different manuals are in subdirectories of the
``docs/src/`` directory.

To build a specific guide, look for a ``pom.xml`` file within a subdirectory,
then run the ``mvn`` command in that directory. For example::

    cd docs/src/glazier-manual
    mvn clean generate-sources

The generated PDF documentation file is::

    docs/src/glazier-manual/src/target/docbkx/pdf/glazier-manual.pdf

The root of the generated HTML documentation is::

    docs/src/glazier-manual/src/target/docbkx/webhelp/glazier-manual/content/index.html

Installing
==========
Refer to http://glazier.openstack.org to see where these documents are published
and to learn more about the Glazier project.
