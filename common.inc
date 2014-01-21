#!/bin/bash
#
# Common functions file
#
DEBUGLVL=2
RUN_DIR=${RUN_DIR:-$(cd $(dirname "$0") && pwd)}
LOGFILE="$RUN_DIR/install.log"
PIPAPPS="pip python-pip pip-python"
PIPCMD=""
PIPARGS=""
TRBL_FILE=""

if [ "$DEBUGLVL" -eq 4 ]; then
    set -x
fi
function log {
    if [ "$DEBUGLVL" -gt 0 ]; then
        chars=$(echo "@$" | wc -c)
        case $DEBUGLVL in
            1)
                echo -e "LOG:>$@"
                ;;
            2)
                echo -e "$(date +"%m-%d-%Y %H:%M") LOG:>$@" | tee --append $LOGFILE
                ;;
            3)
                echo -e "$(date +"%m-%d-%Y %H:%M") LOG:>$@" >> $LOGFILE
                ;;
            4)
                echo -e "$(date +"%m-%d-%Y %H:%M") LOG:>$@" | tee --append $LOGFILE
                ;;
        esac
    fi
}
function lowercase(){
    echo "$1" | sed "y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/"
}
function get_os(){
    KERNEL=$(uname -r)
    MACH=$(uname -m)
    OS=$(uname)
    if [ "${OS}" = "Linux" ] ; then
        if [ -f /etc/redhat-release ] ; then
            DISTRO_BASED_ON='RedHat'
            PACKAGER='yum'
            PKG_MGR='rpm'
            DIST=$(cat /etc/redhat-release |sed s/\ release.*//)
            PSUEDONAME=$(cat /etc/redhat-release | sed s/.*\(// | sed s/\)//)
            REV=$(cat /etc/redhat-release | sed s/.*release\ // | sed s/\ .*//)
        elif [ -f /etc/SuSE-release ] ; then
            DISTRO_BASED_ON='SuSe'
            PACKAGER='zypper'
            PKG_MGR='rpm'
            PSUEDONAME=$(cat /etc/SuSE-release | tr "\n" ' '| sed s/VERSION.*//)
            REV=$(cat /etc/SuSE-release | tr "\n" ' ' | sed s/.*=\ //)
        elif [ -f /etc/debian_version ] ; then
            DISTRO_BASED_ON='Debian'
            PACKAGER='apt-get'
            PKG_MGR='dpkg'
            DIST=$(cat /etc/lsb-release | grep '^DISTRIB_ID' | awk -F=  '{ print $2 }')
            PSUEDONAME=$(cat /etc/lsb-release | grep '^DISTRIB_CODENAME' | awk -F=  '{ print $2 }')
            REV=$(cat /etc/lsb-release | grep '^DISTRIB_RELEASE' | awk -F=  '{ print $2 }')
        fi
        if [ -f /etc/UnitedLinux-release ] ; then
            DIST="${DIST}[$(cat /etc/UnitedLinux-release | tr "\n" ' ' | sed s/VERSION.*//)]"
        fi
        OS=$(lowercase $OS)
        DISTRO_BASED_ON=$(lowercase $DISTRO_BASED_ON)
        readonly OS
        readonly DIST
        readonly DISTRO_BASED_ON
        readonly PSUEDONAME
        readonly REV
        readonly KERNEL
        readonly MACH
        #readonly PACKAGER
    else
        OS=unknown
        readonly OS
        log "Unsupported OS:\"$OS\", sorry, exiting!"
        exit 1
    fi
}
function find_or_install()
{
    _searching_for=$1
    _pkg_mrg_cmd=''
    _pkgr_cmd=''
    retval=0
    case $(lowercase $DISTRO_BASED_ON) in
        "debian")
            _pkg_mrg_cmd="$PKG_MGR -s $_searching_for"
            _pkgr_cmd="$PACKAGER install $_searching_for --yes"
            ;;
        *)
            _pkg_mrg_cmd="$PKG_MGR -q $_searching_for"
            _pkgr_cmd="$PACKAGER install $_searching_for -y"
            ;;
    esac
    $_pkg_mrg_cmd > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log "Package \"$_searching_for\" already installed"
        retval=2
    else
        log "Installing \"$_searching_for\"..."
        $_pkgr_cmd > /dev/null 2>&1
        if [ $? -ne 0 ];then
            log "...installation fails, exiting!"
            retval=1
        else
            log "...success"
            retval=0
        fi
    fi
    return $retval
}
function is_py_package_installed()
{
    retval=0
    py_pkg=$1
    found_pkg=$($PIPCMD freeze | grep -E "^$py_pkg")
    if [ $? -ne 0 ]; then
        retval=1
    fi
    echo $found_pkg
    return $retval
}
function genpass()
{
    echo $(date | md5sum |head -c${5:-13})
}
function shslash()
{
    echo $1 | sed 's/\//\\\//g'
}
function split()
{
    # Prefix local names with the function name to try to avoid conflicts
    # local split_wordlist
    split_wordlist="$1"
    shift
    read "$@" <<EOF-split-end-of-arguments
${split_wordlist}
EOF-split-end-of-arguments
}
# Returns true if v1 >= v2, false if v1 < v2
function version_ge()
{
    # Prefix local names with the function name to try to avoid conflicts
    # local version_ge_1 version_ge_2 version_ge_a version_ge_b
    # local version_ge_save_ifs
    version_ge_v1="$1"
    version_ge_v2="$2"
    version_ge_save_ifs="$IFS"
    while test -n "${version_ge_v1}${version_ge_v2}"; do
        IFS="."
        split "$version_ge_v1" version_ge_a version_ge_v1
        split "$version_ge_v2" version_ge_b version_ge_v2
        IFS="$version_ge_save_ifs"
        #echo " compare  $version_ge_a  $version_ge_b"
        test "0$version_ge_a" -gt "0$version_ge_b" && return 0 # v1>v2: true
        test "0$version_ge_a" -lt "0$version_ge_b" && return 1 # v1<v2:false
    done
    # version strings are both empty & no differences found - must be equal.
    return 0 # v1==v2: true
}
function find_pip()
{
    _pipargs=""
    pip_min_ver="1.4"
    for cmd in $PIPAPPS
    do
        _cmd=$(which $cmd 2>/dev/null)
        if [ $? -eq 0 ];then
                break
        fi
    done
    if [ -z "$_cmd" ];then
        echo "Can't find \"pip\" in system, please install it first, exiting!"
        exit 1
    else
        _pip_ver=$($_cmd --version | grep -oE "[0-9]\.[0-9]" | head -n1)
        if [ -n "$_pip_ver" ]; then
            version_ge $_pip_ver $pip_min_ver
            if [ $? -ne 0 ]; then
                log "Upgrading pip ..."
                $_cmd install --upgrade pip==$pip_min_ver
                if [ $? -ne 0 ]; then
                    log "...pip upgrade fails, exiting!"
                    exit 1
                else
                    log "...success"
                    sleep 2
                    for cmd in $PIPAPPS
                    do
                        _cmd=$(which $cmd 2>/dev/null)
                        if [ $? -eq 0 ];then
                            break
                        fi
                    done
                fi
            fi
            _pip_ver=$($_cmd --version | grep -oE "[0-9]\.[0-9]" | head -n1)
            version_ge $_pip_ver "1.5"
            if [ $? -eq 0 ]; then
                log "For future use, sorry, use pip v$pip_min_ver, exiting!"
                exit 1
                ##_pipargs="--allow-unverified --allow-external"
                #_pipargs="--allow-all-external"
                #mk_dir "/root/.pip"
                #_pipcfg="/root/.pip/pip.conf"
                #if [ ! -f "$_pipcfg" ]; then
                #    touch $_pipcfg
                #fi
                #iniset 'install' 'allow-all-external' 'true' "$_pipcfg"
                #iniset 'install' 'allow-all-unverified' 'true' "$_pipcfg"
                #log "Setuptools upgrade required..."
                #$cmd install setuptools --no-use-wheel --upgrade >> $LOGFILE 2>&1
                #if [ $? -ne 0 ]; then
                #    log "...upgrade fails, exiting"
                #    exit 1
                #else
                #    log "...success"
                #fi
            fi
            log "Found pip version - $_pip_ver"
        fi
        PIPARGS=$_pipargs
        PIPCMD=$_cmd
    fi
}
function add_daemon_credentials()
{
    retval=0
    daemonuser=${1:-murano}
    daemongroup=${2:-murano}
    daemonhomedir=${3:-/home/$daemonuser}
    getent group $daemongroup > /dev/null
    if [ $? -ne 0 ]; then
        log "Creating group \"$daemongroup\"..."
        groupadd -r $daemongroup
        if [ $? -eq 0 ]; then
            log "...success"
        else
            log "Can't create \"$daemongroup\", exiting!"
            retval=1
            exit 1
        fi
    else
        log "Group \"$daemongroup\" exists"
    fi
    getent passwd $daemonuser > /dev/null
    if [ $? -ne 0 ]; then
        log "Creating user \"$daemonuser\"..."
        useradd -r -g $daemongroup -G $daemongroup -d $daemonhomedir -s $(which nologin) -c "Murano Daemons" $daemonuser
        if [ $? -eq 0 ]; then
            log "...success"
        else
            log "Can't create \"$daemonuser\", exiting!"
            retval=1
            exit 1
        fi
    else
        log "User \"$daemonuser\" exists"
    fi
    return $retval
}
function remove_daemon_credentials()
{
    retval=0
    daemonuser=${1:-murano}
    daemongroup=${2:-murano}
    daemonhomedir=${3:-/home/$daemonuser}
    getent passwd $daemonuser > /dev/null
    if [ $? -eq 0 ]; then
        log "Deleting user \"$daemonuser\"..."
        userdel -f $daemonuser
        if [ $? -eq 0 ]; then
            if [ -d "$daemonhomedir" ]; then
                rm -rf $daemonhomedir
            fi
            log "...success"
        else
            log "Can't delete \"$daemonuser\", exiting!"
            retval=1
            exit 1
        fi
    fi
    getent group $daemongroup > /dev/null
    if [ $? -eq 0 ]; then
        log "Deleting group \"$daemongroup\"..."
        groupdel $daemongroup
        if [ $? -eq 0 ]; then
            log "...success"
        else
            log "Can't delete \"$daemongroup\", exiting!"
            retval=1
            exit 1
        fi
    fi
    return $retval
}
function iniset()
{
    local section=$1
    local option=$2
    local value=$3
    local file=$4
    local line

    if [ -z "$section" ] ; then
        # No section name specified
        sed -i -e "s/^\($option[ \t]*=[ \t]*\).*$/\1$value/" "$file"
    else
        # Check if section already exists
        if ! grep -q "^\[$section\]" "$file" ; then
            # Add section at the end
            echo -e "\n[$section]" >>"$file"
        fi

        # Check if parameter in the section exists
        line=$(sed -ne "/^\[$section\]/,/^\[.*\]/ { /^$option[ \t]*=/ p; }" "$file")
        if [ -z "$line" ] ; then
            # Add parameter if it is not exists
            sed -i -e "/^\[$section\]/ a\\
$option = $value
" "$file"
        else
            # Replace existing parameter
            sed -i -e "/^\[$section\]/,/^\[.*\]/ s|^\($option[ \t]*=[ \t]*\).*$|\1$value|" "$file"
        fi
    fi
}
function mk_dir()
{
    retval=0
    path_to_check=$1
    if [ -d "$path_to_check" ]; then
        log "Path \"$path_to_check\" already exists."
    elif [ -f "$path_to_check" ]; then
        log "Path \"path_to_check\" is an existing file, exiting!"
        exit 1
    else
        mkdir -p "$path_to_check"
        if [ $? -ne 0 ]; then
            log "Can't create \"$path_to_check\", exiting!"
            retval=1
            exit 1
        fi
    fi
    if [ $# -eq 3 ]; then
        owner_user=$2
        owner_group=$3
        chown -R $owner_user:$owner_group $path_to_check
        if [ $? -ne 0 ]; then
            log "Can't set ownership to \"$owner_user:$owner_group\" for \"$path_to_check\", exiting!"
            retval=1
            exit 1
        fi
    fi
    return $retval
}
function get_service_exec_path()
{
    retval=0
    if [ -z "$SERVICE_EXEC_PATH" ]; then
        SERVICE_EXEC_PATH=$(which $DAEMON_NAME)
        if [ $? -ne 0 ]; then
            log "Can't find \"$DAEMON_NAME\", please install the \"$SERVICE_SRV_NAME\" by running \"$(basename "$0") install\" or set variable SERVICE_EXEC_PATH=/path/to/daemon before running setup script, exiting!"
            retval=1
        fi
    else
        if [ ! -x "$SERVICE_EXEC_PATH" ]; then
            log "\"$SERVICE_EXEC_PATH\" in not executable, please install the \"$DAEMON_NAME\" or set variable SERVICE_EXEC_PATH=/path/to/daemon before running setup script, exiting!"
            retval=1
        fi
    fi
    return $retval
}
