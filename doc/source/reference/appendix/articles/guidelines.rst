======================
Development Guidelines
======================

Coding Guidelines
-----------------

For all the code in Murano we have a rule - it should pass `PEP 8`_.

To check your code against PEP 8 run:

::

    tox -e pep8


.. seealso::

   * https://pep8.readthedocs.org/en/latest/
   * https://flake8.readthedocs.org
   * https://docs.openstack.org/hacking/latest/

Blueprints and Specs
--------------------

Murano team uses the `murano-specs`_ repository for its blueprint and
specification (specs) review process. See `Launchpad`_ to propose or
see the status of a current blueprint.

Testing Guidelines
------------------

Murano has a suite of tests that are run on all submitted code,
and it is recommended that developers execute the tests themselves to
catch regressions early.  Developers are also expected to keep the
test suite up-to-date with any submitted code changes.

Unit tests are located at ``murano/tests``.

Murano's suite of unit tests can be executed in an isolated environment
with `Tox`_. To execute the unit tests run the following from the root of
Murano repo on Python 2.7:

::

    tox -e py27


Documentation Guidelines
------------------------

Murano dev-docs are written using Sphinx / RST and located in the main repo
in ``doc`` directory.

The documentation in docstrings should follow the `PEP 257`_ conventions
(as mentioned in the `PEP 8`_ guidelines).

More specifically:

1. Triple quotes should be used for all docstrings.
2. If the docstring is simple and fits on one line, then just use
   one line.
3. For docstrings that take multiple lines, there should be a newline
   after the opening quotes, and before the closing quotes.
4. `Sphinx`_ is used to build documentation, so use the restructured text
   markup to designate parameters, return values, etc.  Documentation on
   the sphinx specific markup can be found here:



Run the following command to build docs locally.

::

    tox -e docs


.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _PEP 257: http://www.python.org/dev/peps/pep-0257/
.. _Tox: http://tox.testrun.org/
.. _Sphinx: http://sphinx.pocoo.org/markup/index.html
.. _murano-specs: http://git.openstack.org/cgit/openstack/murano-specs
.. _Launchpad: http://blueprints.launchpad.net/murano
