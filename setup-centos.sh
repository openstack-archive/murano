#!/bin/sh
#    Copyright (c) 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
#    CentOS script.

LOGLVL=1
SERVICE_CONTENT_DIRECTORY=`cd $(dirname "$0") && pwd`
PREREQ_PKGS="upstart wget git make python-pip python-devel mysql-connector-python libxml2-devel libxslt-devel libffi-devel"
PIPAPPS="pip python-pip pip-python"
PIPCMD=""
SERVICE_SRV_NAME="murano-api"
GIT_CLONE_DIR=`echo $SERVICE_CONTENT_DIRECTORY | sed -e "s/$SERVICE_SRV_NAME//"`
ETC_CFG_DIR="/etc/$SERVICE_SRV_NAME"
SERVICE_CONFIG_FILE_PATH="$ETC_CFG_DIR/murano-api.conf"

# Functions
# Loger function
log()
{
	MSG=$1
	if [ $LOGLVL -gt 0 ]; then
		echo "LOG:> $MSG"
	fi
}

# Check or install package
in_sys_pkg()
{
	PKG=$1
	rpm -q $PKG > /dev/null 2>&1
	if [ $? -eq 0 ]; then
	    log "Package \"$PKG\" already installed"
	else
	    log "Installing \"$PKG\"..."
	    yum install $PKG --assumeyes > /dev/null 2>&1
	    if [ $? -ne 0 ];then
	        log "installation fails, exiting!!!"
	        exit 1
		fi
	fi
}

# find pip
find_pip()
{
        for cmd in $PIPAPPS
        do
                _cmd=$(which $cmd 2>/dev/null)
                if [ $? -eq 0 ];then
                        break
                fi
        done
        if [ -z $_cmd ];then
                echo "Can't find \"pip\" in system, please install it first, exiting!"
                exit 1
        else
                PIPCMD=$_cmd
        fi
}

# git clone
gitclone()
{
	FROM=$1
	CLONEROOT=$2
	log "Cloning from \"$FROM\" repo to \"$CLONEROOT\""
	cd $CLONEROOT && git clone $FROM > /dev/null 2>&1
	if [ $? -ne 0 ];then
        	log "cloning from \"$FROM\" fails, exiting!!!"
        	exit
        fi
}

# install
inst()
{
CLONE_FROM_GIT=$1
# Checking packages
	for PKG in $PREREQ_PKGS
	do
		in_sys_pkg $PKG
	done
# Find python pip
	find_pip
# If clone from git set
	if [ ! -z $CLONE_FROM_GIT ]; then
# Preparing clone root directory
	if [ ! -d $GIT_CLONE_DIR ]; then
		log "Creting $GIT_CLONE_DIR direcory..."
		mkdir -p $GIT_CLONE_DIR
		if [ $? -ne 0 ]; then
			log "Can't create $GIT_CLONE_DIR, exiting!!!"
			exit
		fi
	fi
# Cloning from GIT
		GIT_WEBPATH_PRFX="https://github.com/stackforge/"
		gitclone "$GIT_WEBPATH_PRFX$SERVICE_SRV_NAME.git" $GIT_CLONE_DIR
# End clone from git section
	fi

# Setupping...
	log "Running setup.py"
	MRN_CND_SPY=$SERVICE_CONTENT_DIRECTORY/setup.py
	if [ -e $MRN_CND_SPY ]; then
		chmod +x $MRN_CND_SPY
		log "$MRN_CND_SPY output:_____________________________________________________________"		
## Setup through pip
		# Creating tarball
		rm -rf $SERVICE_CONTENT_DIRECTORY/*.egg-info
		cd $SERVICE_CONTENT_DIRECTORY && python $MRN_CND_SPY egg_info
                if [ $? -ne 0 ];then
                        log "\"$MRN_CND_SPY\" egg info creation FAILS, exiting!!!"
                        exit 1
                fi
		rm -rf $SERVICE_CONTENT_DIRECTORY/dist/*
		cd $SERVICE_CONTENT_DIRECTORY && $MRN_CND_SPY sdist
		if [ $? -ne 0 ];then
			log "\"$MRN_CND_SPY\" tarball creation FAILS, exiting!!!"
			exit 1
		fi
		# Running tarball install
		TRBL_FILE=$(basename `ls $SERVICE_CONTENT_DIRECTORY/dist/*.tar.gz`)
		$PIPCMD install $SERVICE_CONTENT_DIRECTORY/dist/$TRBL_FILE
		if [ $? -ne 0 ];then
			log "$PIPCMD install \"$TRBL_FILE\" FAILS, exiting!!!"
			exit 1
		fi
	else
		log "$MRN_CND_SPY not found!"
	fi
# Creating etc directory for config files
	if [ ! -d $ETC_CFG_DIR ]; then
	    log "Creting $ETC_CFG_DIR direcory..."
	    mkdir -p $ETC_CFG_DIR
	    if [ $? -ne 0 ]; then
	        log "Can't create $ETC_CFG_DIR, exiting!!!"
	        exit
	    fi
    fi
# making smaple configs 
    log "Making sample configuration files at \"$ETC_CFG_DIR\""
	for file in `ls $SERVICE_CONTENT_DIRECTORY/etc`
	do
		cp -f "$SERVICE_CONTENT_DIRECTORY/etc/$file" "$ETC_CFG_DIR/$file.sample"
	done
}

# searching for service executable in path
get_service_exec_path()
{
	if [ -z "$SERVICE_EXEC_PATH" ]; then
		SERVICE_EXEC_PATH=`which $SERVICE_SRV_NAME`
		if [ $? -ne 0 ]; then
			log "Can't find \"$SERVICE_SRV_NAME\", please install the \"$SERVICE_SRV_NAME\" by running \"$(basename "$0") install\" or set variable SERVICE_EXEC_PATH=/path/to/daemon before running setup script, exiting!"
			exit 1
		fi
	else
		if [ ! -x "$SERVICE_EXEC_PATH" ]; then
			log "\"$SERVICE_EXEC_PATH\" in not executable, please install the \"$SERVICE_SRV_NAME\" or set variable SERVICE_EXEC_PATH=/path/to/daemon before running setup script, exiting!"
			exit 1
		fi
	fi
}

# inject init
injectinit()
{
echo "description \"$SERVICE_SRV_NAME service\"
author \"Igor Yozhikov <iyozhikov@mirantis.com>\"
start on runlevel [2345]
stop on runlevel [!2345]
respawn
exec $SERVICE_EXEC_PATH --config-file=$SERVICE_CONFIG_FILE_PATH" > "/etc/init/$SERVICE_SRV_NAME.conf"
    log "Reloading initctl"
    initctl reload-configuration
}

# purge init
purgeinit()
{
    rm -f /etc/init/$SERVICE_SRV_NAME.conf
    log "Reloading initctl"
    initctl reload-configuration
}

# uninstall
uninst()
{
	# Uninstall trough  pip
        find_pip
	# looking up for python package installed
	PYPKG=`echo $SERVICE_SRV_NAME | tr -d '-'`
	_pkg=$($PIPCMD freeze | grep $PYPKG)
	if [ $? -eq 0 ]; then
		log "Removing package \"$PYPKG\" with pip"
		$PIPCMD uninstall $_pkg --yes
	else
		log "Python package \"$PYPKG\" not found"
	fi
}

# postinstall
postinst()
{
	log "Please, make proper configugation,located at \"$ETC_CFG_DIR\", before starting the \"$SERVICE_SRV_NAME\" daemon!"
}
# Command line args'
COMMAND="$1"
case $COMMAND in
	inject-init )
		get_service_exec_path
		log "Injecting \"$SERVICE_SRV_NAME\" to init..."
		injectinit
		postinst
		;;

	install )
		inst
		get_service_exec_path
		injectinit
		postinst
		;;

	installfromgit )
		inst "yes"
		get_service_exec_path
		injectinit
		postinst
		;;

	purge-init )
		log "Purging \"$SERVICE_SRV_NAME\" from init..."
		stop $SERVICE_SRV_NAME
		purgeinit
		;;

	uninstall )
		log "Uninstalling \"$SERVICE_SRV_NAME\" from system..."
		stop $SERVICE_SRV_NAME
		purgeinit
		uninst
		;;

	* )
		echo -e "Usage: $(basename "$0") command \nCommands:\n\tinstall - Install $SERVICE_SRV_NAME software\n\tuninstall - Uninstall $SERVICE_SRV_NAME software\n\tinject-init - Add $SERVICE_SRV_NAME to the system start-up\n\tpurge-init - Remove $SERVICE_SRV_NAME from the system start-up"
		exit 1
		;;
esac
