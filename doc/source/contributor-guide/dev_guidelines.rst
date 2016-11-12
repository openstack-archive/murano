.. _dev-guidelines:

======================
Development guidelines
======================

Conventions
~~~~~~~~~~~

High-level overview of Murano components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Coding guidelines
~~~~~~~~~~~~~~~~~

There are several significant rules for the Murano developer:

* Follow PEP8 and OpenStack style guidelines.

* Do not import functions. Only module imports are accepted.

* Make commits as small as possible. It speeds up review of the change.

* Six library usage rule: use it only when really necessary (for example if
  existing code will not work in python 3 at all).

* Mark application name in the 1st line of commit message for murano-apps
  repository, i.e. [Apache] or [Kubernetes].

* Prefer code readability over performance unless the situations when
  performance penalty can be proven to be big.

* Write Py3-compatible code. If that's impossible leave comment.

Rules for MuranoPL coding style:

* Use camelCase for MuranoPL functions/namespaces/variables/properties,
  PascalCase for class names.

* Consider using ``$this`` instead of ``$`` where appropriate.

Debug tips
~~~~~~~~~~
