#!/bin/bash

source ./run_tests_common.sh

# Using .venv for tempest installation
pushd $TEMPEST_DIR
python tools/install_venv.py
source .venv/bin/activate
pip install nose
nosetests -sv /opt/stack/new/murano/murano/tests/functional/api/v1
RETVAL=$?
deactivate
popd
exit $RETVAL

