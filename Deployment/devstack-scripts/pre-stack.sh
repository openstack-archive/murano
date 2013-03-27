#!/bin/bash

if [ -z "$1" ] ; then
    source ./localrc
fi


# Executing pre-stack actions
#===============================================================================

# Executing checks
#-----------------
die_if_not_set DEVSTACK_DIR
die_if_not_set MYSQL_DB_TMPFS_SIZE
die_if_not_set NOVA_CACHE_TMPFS_SIZE
#-----------------


restart_service dbus rabbitmq-server


# Moving MySQL database to tmpfs
#-------------------------------
if [[ $(trueorfalse True $MYSQL_DB_TMPFS) = "True" ]] ; then
    die_if_not_set MYSQL_DB_TMPFS_SIZE
    mount_dir=/var/lib/mysql
    sudo -s << EOF
        echo "Stopping MySQL Server"
        service mysql stop
    
        umount $mount_dir
        mount -t tmpfs -o size=$MYSQL_DB_TMPFS_SIZE tmpfs $mount_dir
        chmod 700 $mount_dir
        chown mysql:mysql $mount_dir

        mysql_install_db

        /usr/bin/mysqld_safe --skip-grant-tables &
        sleep 5
EOF

    sudo mysql << EOF
        FLUSH PRIVILEGES;
        SET PASSWORD FOR 'root'@'localhost' = PASSWORD('swordfish');
        SET PASSWORD FOR 'root'@'127.0.0.1' = PASSWORD('swordfish');
EOF

    sudo -s << EOF
        killall mysqld
        sleep 5

        echo "Starting MySQL Server"
        service mysql start
EOF
else
    echo "MYSQL_DB_TMPFS = '$MYSQL_DB_TMPFS'"
fi
#-------------------------------


# Devstack log folder
#--------------------
sudo -s << EOF
    mkdir -p $SCREEN_LOGDIR
    chown stack:stack $SCREEN_LOGDIR
EOF
#--------------------


# Moving nova images cache to tmpfs
#----------------------------------
if [[ $(trueorfalse True $NOVA_CACHE_TMPFS) = "True" ]] ; then
    die_if_not_set NOVA_CACHE_TMPFS_SIZE
    mount_dir=/opt/stack/data/nova/instances
    sudo -s << EOF
        umount $mount_dir
        mount -t tmpfs -o size=$NOVA_CACHE_TMPFS_SIZE tmpfs $mount_dir
        chmod 775 $mount_dir
        chown stack:stack $mount_dir
EOF
else
    echo "NOVA_CACHE_TMPFS = '$NOVA_CACHE_TMPFS'"
fi

#----------------------------------


# Replacing devstack's localrc config
#------------------------------------
if [[ -f "devstack.localrc" ]] ; then
    rm -f "$DEVSTACK_DIR/localrc"
    cp devstack.localrc "$DEVSTACK_DIR/localrc"
else
    echo "File 'devstack.localrc' not found!"
fi
#------------------------------------

#===============================================================================

