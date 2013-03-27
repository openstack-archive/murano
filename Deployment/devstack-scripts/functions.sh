#!/bin/bash



# Test if the named environment variable is set and not zero length
# is_set env-var
#function is_set() {
#    local var=\$"$1"
#    eval "[ -n \"$var\" ]" # For ex.: sh -c "[ -n \"$var\" ]" would be better, but several exercises depends on this
#}



# Prints "message" and exits
# die "message"
#function die() {
#    local exitcode=$?
#    if [ $exitcode == 0 ]; then
#        exitcode=1
#    fi
#    set +o xtrace
#    local msg="[ERROR] $0:$1 $2"
#    echo $msg 1>&2;
#    if [[ -n ${SCREEN_LOGDIR} ]]; then
#        echo $msg >> "${SCREEN_LOGDIR}/error.log"
#    fi
#    exit $exitcode
#}



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
        echo "Restarting service '$1' ..."
        sudo service $1 restart
        shift 1
    done
}



# Normalize config values to True or False
# Accepts as False: 0 no false False FALSE
# Accepts as True: 1 yes true True TRUE
# VAR=$(trueorfalse default-value test-value)
#function trueorfalse() {
#    local default=$1
#    local testval=$2
#
#    [[ -z "$testval" ]] && { echo "$default"; return; }
#    [[ "0 no false False FALSE" =~ "$testval" ]] && { echo "False"; return; }
#    [[ "1 yes true True TRUE" =~ "$testval" ]] && { echo "True"; return; }
#    echo "$default"
#}


