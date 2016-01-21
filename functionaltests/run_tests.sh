#!/bin/bash

source ./run_tests_common.sh

MURANO_ROOT=/opt/stack/new/murano/murano
# Using .venv for tempest installation
pushd $TEMPEST_DIR
python "$MURANO_ROOT/tools/install_venv.py"
source "$MURANO_ROOT/.venv/bin/activate"
pip install nose
nosetests -sv "$MURANO_ROOT/tests/functional/api/v1"
RETVAL=$?
deactivate
popd
exit $RETVAL

