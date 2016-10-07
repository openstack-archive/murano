==========================================
My first Murano App getting started  guide
==========================================

This directory contains the "My first Murano App getting started  guide"
tutorial.

The tutorials work with an application that can be found in the
`openstack/murano-apps <http://git.openstack.org/cgit/openstack/murano-apps/tree/Plone/package>`_
repository.

Prerequisites
-------------

To build the documentation, you must install the Graphviz package.

/source
~~~~~~~

The :code:`/source` directory contains the tutorial documentation as
`reStructuredText <http://docutils.sourceforge.net/rst.html>`_ (RST).

To build the documentation, you must install `Sphinx <http://sphinx-doc.org/>`_ and the
`OpenStack docs.openstack.org Sphinx theme (openstackdocstheme) <https://pypi.python.org/pypi/openstackdocstheme/>`_. When
you invoke tox, these dependencies are automatically pulled in from the
top-level :code:`test-requirements.txt`.

You must also install `Graphviz <http://www.graphviz.org/>`_ on your build system.

The following command invokes :code:`sphinx-build` with :code:`murano-firstapp`::

  tox -e murano-firstapp

/samples
~~~~~~~~

The code samples in this guide are located in this directory.

/build/murano-firstapp
~~~~~~~~~~~~~~~~~~~~~~

The HTML documentation is built in this directory. The :code:`.gitignore` file
for the project specifies this directory.
