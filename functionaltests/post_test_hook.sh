#!/bin/bash

# This script is executed inside post_test_hook function in devstack gate.

cd /opt/stack/new/murano/functionaltests

# Allow to execute other run_tests_*.sh script based on first parameter
RUN_TEST_SUFFIX=""
if [ "$#" -ge 1 ]; then
    RUN_TEST_SUFFIX=_$1
fi
sudo ./run_tests$RUN_TEST_SUFFIX.sh
RETVAL=$?

# Copy tempest log files to be published among other logs upon job completion
sudo cp /opt/stack/new/murano/functionaltests/tempest.log /opt/stack/logs

exit $RETVAL
