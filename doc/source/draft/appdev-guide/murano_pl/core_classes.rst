.. _core_classes:

Core library
~~~~~~~~~~~~

You can use some objects and actions in several application
deployments. All common parts are grouped into MuranoPL libraries.
Murano core library is a set of classes needed in every deployment as
helpers for application classes. This library is located under the
`meta <http://git.openstack.org/cgit/openstack/murano/tree/meta/io.murano/>`_
directory.

Logging API
-----------

Logging API is the part of core library since Liberty release. It was
introduced to improve debuggability of MuranoPL programs.

You can get a logger instance by calling a ``logger`` function which is located
in  ``io.murano.system`` namespace. The ``logger`` function takes a logger name as the
only parameter. It is a common recommendation to use full class name as a
logger name within that class. This convention avoids names conflicts
in logs and ensures a better logging subsystem configurability.

Logger class instantiation::

    $log: logger('io.murano.apps.activeDirectory.ActiveDirectory')


There are several methods you can use for logging events: ``debug``,
``trace``, ``info``, ``warning``, ``error``, ``critical`` that correspond
to the log levels.

Log levels prioritized in order of severity:

============  ===========
Level         Description
============  ===========
CRITICAL      The CRITICAL level designates very severe error events that will presumably lead the application to abort.
ERROR         The ERROR level designates error events that might still allow the application to continue running.
INFO          The INFO level designates informational messages that highlight the progress of the application at the coarse-grained level.
DEBUG         The DEBUG level designates fine-grained informational events that are most useful to debug an application.
TRACE         The TRACE level designates finer-grained informational events than the DEBUG level.
============  ===========

Logging example::

    $log.info('print my info message {message}', message=>message)

Logging methods use the same format rules as the YAQL ``format`` function.
Thus the line above is equal to the::

    $log.info('print my info message {message}'.format(message=>message))

To print an exception stacktrace, use the ``exception`` method.
This method uses the `ERROR` level.

Logging exception::

  Try:
    - Throw: exceptionName
      Message: exception message
  Catch:
  With: exceptionName
  As: e
  Do:
    - $log.exception($e, 'something bad happen "{message}"', message=>message)


.. NOTE::
    You can configure the logging subsystem via `logging.conf` of the Murano
    Engine. The Murano Engine configuration lays beyond the MuranoPL tutorial.
    Refer to the Murano or the oslo.log tutorials for more information on how
    to configure logs.
