=============================
OASIS TOSCA Plugin for Murano
=============================
This is a plugin for Murano to support the OASIS standard for TOSCA. The
feature currently supported by this plugin is importing Murano application
definition archives of TOSCA CSARs into Murano application catalog.


**********
How To Use
**********
In order to make use of this plugin it has to be installed first, in the same
Python environment that Murano is running, using the pip command (i.e., run
*pip install .* from inside the plugin folder). At a minimum, the plugin
requires version *0.2.0* of the *TOSCA-Parser PyPI package*.

Two sample Murano application definition archives are provided in unzip format:

* hello_world
* wordpress

In order to import the corresponding archives refer to *README.rst* inside each
sample folder to generate the archives first. The archives then will be ready
to be imported into Murano application catalog via Murano command line or
Murano UI.
