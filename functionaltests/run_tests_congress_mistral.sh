#!/bin/bash

source ./run_tests_common.sh

# Add tempest source tree to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$TEMPEST_DIR

# Add tempest config file path to env variables
export TEMPEST_CONFIG_DIR=${TEMPEST_CONFIG_DIR:-$TEMPEST_DIR/etc/}

#installing requirements for tempest
pip install -r $TEMPEST_DIR/requirements.txt

#installing test requirements for murano
pip install -r ../test-requirements.txt

nosetests -sv ../murano/tests/functional/integration/test_policy_enf.py ../murano/tests/functional/integration/test_mistral.py
