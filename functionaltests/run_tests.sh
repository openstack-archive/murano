#!/bin/bash

source ./run_tests_common.sh

nosetests -sv ../murano/murano/tests/functional/api/v1
RETVAL=$?
deactivate
popd
exit $RETVAL
