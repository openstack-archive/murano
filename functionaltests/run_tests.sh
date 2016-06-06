#!/bin/bash

source ./run_tests_common.sh

# Using .venv for tempest installation
pushd ..
python tools/install_venv.py
source .venv/bin/activate
# force compatible tempest version
pip install nose
pushd $TEMPEST_DIR
git checkout 12.0.0
pip install -r requirements.txt
pip install -r test-requirements.txt
nosetests -sv /opt/stack/new/murano/murano/tests/functional/api/v1
RETVAL=$?
deactivate
popd
popd
exit $RETVAL

