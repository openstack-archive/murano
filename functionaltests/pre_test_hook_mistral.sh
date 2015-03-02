#!/bin/bash

# Install Mistral devstack integration
source ./pre_test_hook_common.sh
MISTRAL_BASE=/opt/stack/new/mistral/contrib/devstack
cp $MISTRAL_BASE/lib/* $DEVSTACK_BASE/lib
cp $MISTRAL_BASE/extras.d/* $DEVSTACK_BASE/extras.d
