#!/bin/bash

source ./run_tests_common.sh

nosetests -sv ../murano/murano/tests/functional/engine/test_policy_enf.py ../murano/murano/tests/functional/engine/test_mistral.py
RETVAL=$?
deactivate
popd
exit $RETVAL