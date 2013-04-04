#!/bin/bash

if [[ -z "$1" ]] ; then
    SCRIPTS_DIR=$( cd $( dirname "$0" ) && pwd )
    source $SCRIPTS_DIR/localrc
fi


# Executing pre-stack actions
#===============================================================================

# Executing checks
#-----------------
die_if_not_set DEVSTACK_DIR
die_if_not_set MYSQL_DB_TMPFS_SIZE
die_if_not_set NOVA_CACHE_TMPFS_SIZE
#-----------------


if [[ ,$INSTALL_MODE, =~ ',standalone,multihost,controller,' ]] ; then
    restart_service dbus rabbitmq-server
fi


if [[ ,$INSTALL_MODE, =~ ',standalone,multihost,controller,' ]] ; then
    move_mysql_data_to_ramdrive
fi


# Devstack log folder
#--------------------
sudo -s << EOF
mkdir -p $SCREEN_LOGDIR
chown stack:stack $SCREEN_LOGDIR
EOF
#--------------------


case $INSTALL_MODE in
    'standalone')
        update_devstack_localrc 'standalone'
    ;;
    'multihost')
        update_devstack_localrc 'controller'
    ;;
    'controller')
        update_devstack_localrc 'controller'
    ;;
    'compute')
        update_devstack_localrc 'compute'
    ;;
esac

#===============================================================================

