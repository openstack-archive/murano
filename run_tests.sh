#!/bin/bash

EXPECTED_TOX_VERSION="1.6.1"

tox_version=`tox --version 2>/dev/null`
if [ $? -ne 0 ]; then
  tox_version="not installed"
else
  tox_version=`echo $tox_version | cut -d' ' -f1`
fi

echo "run_tests.sh is deprecated in favor of running tox directly."
echo "This will ensure your results are the same as Jenkins'."
echo

if [ "$tox_version" == "not installed" ]; then
  echo "It looks like tox isn't installed. You can install (globally or"
  echo "into a virtualenv) with pip. Be sure to install version 1.6.1,"
  echo "since later versions have problems running some tests. To install:"
  echo
  echo "  pip install \"tox==1.6.1\""
  echo
elif [ "$tox_version" != "$EXPECTED_TOX_VERSION" ]; then
  echo "## WARNING ##"
  echo "You have tox version $tox_version installed. Consider installing"
  echo "version $EXPECTED_TOX_VERSION, since later versions may not run tests correctly."
  echo
else
  echo "You have tox $tox_version installed."
  echo
fi

echo "To run unit tests or pep8 using tox:"
echo
echo "  'tox -e pep8' will run style checks"
echo "  'tox -e py26' will run python 2.6 unit tests"
echo "  'tox -e py27' will run python 2.7 unit tests"
echo "  'tox' will run all unit tests and pep8 (as Jenkins does)"
echo
echo "Tox creates its own virtual environments."
echo
echo "To run functional tests, run ./functionaltests/run_tests.sh"


