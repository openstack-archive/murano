.. _exec_plan:

=======================
Execution plan template
=======================

An execution plan template is a set of metadata that describes
the installation process of an application on a virtual
machine. It is a minimal executable unit that can be
triggered in Murano workflows and is understandable to
the Murano agent, which is responsible for receiving,
correctness verification and execution of the statements
included in the template.

The execution plan template is able to trigger any type of script
that executes commands and installs application components
as the result. Each script included in the execution
plan template may consist of a single file or a set of interrelated
files. A single script can be reused across several execution
plans.

This section is devoted to the structure and syntax of an execution
plan template. For different configurations of templates, please
refer to the :ref:`Examples <examples>` section.

Template sections
~~~~~~~~~~~~~~~~~

The table below contains the list of the sections that can be
included in the execution plan template with the description of
their meaning and the default attributes which are used by the
agent if any of the listed parameters is not specified.

==================  ===================================================
  Section name        Meaning and default value
==================  ===================================================
  FormatVersion       a version of the execution plan template syntax
                      format. Default is ``1.0.0``. **Optional**

  Name                a human-readable name for the execution plan to
                      be used for logging. **Optional**

  Version             a version of the execution plan itself, is used
                      for logging and tracing. Each time the content
                      of the template content changes (main script,
                      attached scripts, properties, etc.), the version
                      value should be incremented.
                      This is in contrast with ``FormatVersion``,
                      which is used to distinguish the execution plan
                      format.
                      The default value is ``0.0.0``. **Optional**

  Body                string that represents the Python statement and is
                      executed by the murano-agent. Scripts defined in
                      the Scripts section are invoked from here.
                      **Required**

  Parameters          a dictionary of the ``String->JsonObject`` type
                      that maps parameter names to their values.
                      **Optional**.

  Scripts             a dictionary that maps script names to their
                      script definitions. **Required**
==================  ===================================================


.. _format_version:

FormatVersion property
~~~~~~~~~~~~~~~~~~~~~~

``FormatVersion`` is a property that all other depend on.
That is why it is very important to specify it correctly.

FormatVersion 1.0.0 (default) is still used by Windows murano-agent.
Almost all the applications in murano-apps repository work with FormatVersion
2.0.0. New features that are introduced in Kilo, such as Chef or Puppet,
and downloadable files require version 2.1.0 or greater. Since FormatVersion
2.2.0 it is possible to enable Berkshelf. It requires Mitaka version of agent.
If you omit the ``FormatVersion`` property or put something like ``<2.0.0``,
it will lead to the incorrect behaviour. The same happens if, for example,
``FormatVersion=2.1.0``, and a VM has the pre-Kilo agent.


Scripts section
~~~~~~~~~~~~~~~

Scripts are the building blocks of execution plan templates. As
the name implies those are the scripts for different deployment
platforms.

Each script may consists of one or more files. Those files are
script's program modules, resource files, configs, certificates etc.

Scripts may be executed as a whole (like a single piece of code),
expose some functions that can be independently called in an execution
plan script or both. This depends on deployment platform and executor
capabilities.

Scripts are specified using ``Scripts`` attribute of execution plan.
This attribute maps script name to a structure (document) that describes
the script. It has the following properties:

**Type**
 the name of a deployment platform the script is targeted to.
 The available alternative options for version>=2.1.0 are
 ``Application``, ``Chef``, ``Puppet``, and for version<2.1.0 is
 ``Application`` only. String, required.

**Version**
 the minimum version of the deployment platform/executor required
 by the script. String, optional.

**EntryPoint**
 the name of the script file that is an entry point for this
 execution plan template. String, required.

**Files**
 the filenames of the additional files required for the script. Thus,
 if the script specified  in the ``EntryPoint`` section imports other
 scripts, they should be provided in this section.

 The filenames may include slashes that the agent preserve on VM.
 If a filename is enclosed in the angle brackets (<...>) it will be
 base64-encoded. Otherwise, it will be treated as a plain-text that
 may affect line endings.

 In Kilo, entries for this property may be not just strings but also
 dictionaries (for example, ``filename: URL``) to specify downloadable files
 or git repositories.

 The default value is ``[]`` that means that no extra files are used.
 Array, optional.

**Options**
 an optional dictionary of type ``String->JsonObject`` that contains
 additional options for the script executor. If not provided, an
 empty dictionary is assumed.

 Available alternatives are: ``captureStdout``, ``captureStderr``,
 ``verifyExitcode`` (raise an exception if result is not positive).
 As Options are executor-dependent, these three alternatives
 are available for the Application executor, but may have no sense for
 other types. ``captureStdout``, ``captureStderr`` and ``verifyExitcode``
 require boolean values, and have True as their default values.

 Dictionary, optional.

Please make sure the files specified in EntryPoint and Files sections exist.

.. needs checking, commenting it for now

   Files section
   ~~~~~~~~~~~~~

   Files is an execution plan's entry that describes files that are passed
   as the part of the execution plan template. This is a dictionary that
   maps file ID to a document describing the file.

   It has the following attributes:

   **Name**
    the filename; may include slashes to specify files located in nested
    folders. The root directory is the ``Resources/scripts`` directory.

   **BodyType**
    is one of the following:
     * ``Text``:   Body attribute contains string content of the file
     * ``Base64``: Body attribute contains base64 encoded string content of
        the (binary) file

   **Body**
    contains file data or valid file reference

