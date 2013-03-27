#!/bin/bash

if [[ -z "$1" ]] ; then
    source ./localrc
fi

# Stopping Keero components
#==========================
for serv in conductor portas ; do
    screen -S $SCREEN_NAME -p $serv -X kill
done
#==========================
