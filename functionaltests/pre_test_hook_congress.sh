#!/bin/bash

# Install Congress devstack integration
source ./pre_test_hook_common.sh
CONGRESS_BASE=/opt/stack/new/congress/contrib/devstack
cp $CONGRESS_BASE/lib/* $DEVSTACK_BASE/lib
cp $CONGRESS_BASE/extras.d/* $DEVSTACK_BASE/extras.d

