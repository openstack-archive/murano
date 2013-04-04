#!/bin/bash

SCRIPTS_DIR=$( cd $( dirname "$0" ) && pwd )

source $SCRIPTS_DIR/localrc

INSTALL_MODE="$1"

validate_install_mode



# Update devstack-scripts if multihost
#===============================================================================
if [[ "$INSTALL_MODE" == 'multihost' ]] ; then
    _echo "* Copying devstack-scripts to compute nodes ..."
    for __compute_node in $COMPUTE_NODE_LIST ; do
        _echo "** Removing devstack-scripts on '$__compute_node' ..."
        ssh stack@$__compute_node rm -rf ~/devstack-scripts
        _echo "** Copying devstack-scripts to '$__compute_node' ..."
        scp -r $SCRIPTS_DIR stack@$__compute_node:~/
    done
fi
#===============================================================================



# Executing pre-stack actions
#===============================================================================
_echo "* Executing pre-stack actions ..."
source $SCRIPTS_DIR/pre-stack.sh no-localrc
#===============================================================================



# Creating stack
#===============================================================================
_echo "* Starting devstack ..."
$DEVSTACK_DIR/stack.sh
#===============================================================================



# Executing post-stack actions
#===============================================================================
_echo "* Executing post-stack actions ..."
source $SCRIPTS_DIR/post-stack.sh no-localrc
#source $SCRIPTS_DIR/start-keero.sh no-localrc
#===============================================================================



# Start installation on compute nodes
#===============================================================================
if [[ "$INSTALL_MODE" == 'multihost' ]] ; then
    _echo "* Starting devstack on compute nodes ..."
    for __compute_node in $COMPUTE_NODE_LIST ; do
        _echo "** Starting devstack on '$__compute_node' ..."
        ssh stack@$__compute_node $SCRIPTS_DIR/start-devstack.sh compute
    done
fi
#===============================================================================

