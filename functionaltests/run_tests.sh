#!/bin/bash

source ./run_tests_common.sh

nosetests -sv ../murano/tests/functional/api/v1
