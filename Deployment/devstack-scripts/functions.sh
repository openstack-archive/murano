#!/bin/bash


# Checks an environment variable is not set or has length 0 OR if the
# exit code is non-zero and prints "message" and exits
# NOTE: env-var is the variable name without a '$'
# die_if_not_set env-var "message"
function die_if_not_set() {
    local exitcode=$?
    set +o xtrace
    local evar=$1; shift
    if ! is_set $evar || [ $exitcode != 0 ]; then
        if [[ -z "$1" ]] ; then
            die "Env var '$evar' is not set!"
        else
            die $@
        fi
    fi
}



function restart_service {
    while [[ -n "$1" ]] ; do
        _echo "Restarting service '$1' ..."
        sudo service $1 restart
        shift 1
    done
}



function move_mysql_data_to_ramdrive {
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
        _echo "MYSQL_DB_TMPFS = '$MYSQL_DB_TMPFS'"
    fi
    #-------------------------------
}


function move_nova_cache_to_ramdrive {
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
        _echo "NOVA_CACHE_TMPFS = '$NOVA_CACHE_TMPFS'"
    fi
    #----------------------------------
}


function check_if_folder_exists {
    if [[ ! -d "$1" ]] ; then
        _echo "Folder '$1' not exists!"
        return 1
    fi
    return 0
}


function validate_install_mode {
    case $INSTALL_MODE in
        'standalone')
            check_if_folder_exists "$SCRIPTS_DIR/standalone" || exit
        ;;
        'multihost')
            check_if_folder_exists "$SCRIPTS_DIR/controller" || exit
            check_if_folder_exists "$SCRIPTS_DIR/compute" || exit
        ;;
        'controller')
            check_if_folder_exists "$SCRIPTS_DIR/controller" || exit
        ;;
        'compute')
            check_if_folder_exists "$SCRIPTS_DIR/compute" || exit
        ;;
        *)
            _echo "Wrong install mode '$INSTALL_MODE'"
            exit
        ;;
    esac
}


function update_devstack_localrc {
    local $__install_mode=$1
    
    [[ -z "$__install_mode" ]] \
        && die "Install mode for update_devstack_localrc not provided!"

    # Replacing devstack's localrc config
    #------------------------------------
    devstack_localrc="$SCRIPTS_DIR/$__install_mode/devstack.localrc"
    if [[ -f $devstack_localrc ]] ; then
        rm -f "$DEVSTACK_DIR/localrc"
        cp $devstack_localrc "$DEVSTACK_DIR/localrc"
    else
        _echo "File '$devstack_localrc' not found!"
    fi
    #------------------------------------
}


function _echo {
    echo "[$(hostname)] $@"
}


