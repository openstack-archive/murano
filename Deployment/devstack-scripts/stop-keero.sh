#!/bin/bash

if [[ -z "$1" ]] ; then
    SCRIPTS_DIR=$( cd $( dirname "$0" ) && pwd )
    source $SCRIPTS_DIR/localrc
fi

# Stopping Keero components
#==========================
for serv in conductor portas ; do
    screen -S $SCREEN_NAME -p $serv -X kill
done
#==========================
