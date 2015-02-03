#!/bin/bash

source ./run_tests_common.sh

nosetests -sv ../murano/tests/functional/engine/test_policy_enf.py ../murano/tests/functional/engine/test_mistral.py