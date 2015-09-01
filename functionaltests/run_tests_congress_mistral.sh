#!/bin/bash

source ./run_tests_common.sh

nosetests -sv ../murano/tests/functional/integration/test_policy_enf.py ../murano/tests/functional/integration/test_mistral.py