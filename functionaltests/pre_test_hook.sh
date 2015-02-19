#!/bin/bash

# This script is executed inside pre_test_hook function in desvstack gate.

# Install Murano devstack integration
source ./pre_test_hook_common.sh
MURANO_BASE=/opt/stack/new/murano/contrib/devstack
cp $MURANO_BASE/lib/* $DEVSTACK_BASE/lib
cp $MURANO_BASE/extras.d/* $DEVSTACK_BASE/extras.d

