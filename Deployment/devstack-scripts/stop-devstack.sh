#!/bin/bash

SCRIPTS_DIR=$( cd $( dirname "$0" ) && pwd )

source $SCRIPTS_DIR/localrc

INSTALL_MODE="$1"

validate_install_mode


# Executing pre-unstack actions
#===============================================================================
_echo "* Executing pre-unstack actions ..."
source $SCRIPTS_DIR/pre-unstack.sh no-localrc
#===============================================================================


# Executing unstack.sh 
#===============================================================================
_echo "* Executing stop devstack ..."
$DEVSTACK_DIR/unstack.sh
#===============================================================================


# Executing post-unstack actions
#===============================================================================
_echo "* Executing post-unstack actions ..."
source $SCRIPTS_DIR/post-unstack.sh no-localrc
#source $SCRIPTS_DIR/stop-keero.sh no-localrc
#===============================================================================



# Stop installation on compute nodes
#===============================================================================
if [[ "$INSTALL_MODE" == 'multihost' ]] ; then
    _echo "* Stopping devstack on compute nodes ..."
    for $__compute_node in $COMPUTE_NODE_LIST ; do
        _echo "** Stopping devstack on '$__compute_node' ..."
        ssh stack@$__compute_node $SCRIPTS_DIR/stop-devstack.sh
    done
fi
#===============================================================================

