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
#    Ubuntu script.

LOGLVL=1
SERVICE_CONTENT_DIRECTORY=`cd $(dirname "$0") && pwd`
PREREQ_PKGS="wget git python-pip python-dev python-mysqldb"
SERVICE_SRV_NAME="murano-api"
GIT_CLONE_DIR=`echo $SERVICE_CONTENT_DIRECTORY | sed -e "s/$SERVICE_SRV_NAME//"`
ETC_CFG_DIR="/etc/$SERVICE_SRV_NAME"
SERVICE_CONFIG_FILE_PATH="$ETC_CFG_DIR/murano-api.conf"


if [ -z "$SERVICE_EXEC_PATH" ];then
	SERVICE_EXEC_PATH="/usr/local/bin/murano-api"
fi
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
	dpkg -s $PKG > /dev/null 2>&1
	if [ $? -eq 0 ]; then
	    log "Package \"$PKG\" already installed"
	else
		log "Installing \"$PKG\"..."
		apt-get install $PKG --yes > /dev/null 2>&1
		if [ $? -ne 0 ];then
			log "installation fails, exiting!!!"
			exit
		fi
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

# If clone from git set
	if [ ! -z $CLONE_FROM_GIT ]; then
# Preparing clone root directory
	if [ ! -d $GIT_CLONE_DIR ];then
		log "Creting $GIT_CLONE_DIR direcory..."
		mkdir -p $GIT_CLONE_DIR
		if [ $? -ne 0 ];then
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
	MRN_CND_SPY=$GIT_CLONE_DIR/$SERVICE_SRV_NAME/setup.py
	log $MRN_CND_SPY
	if [ -e $MRN_CND_SPY ];then
		chmod +x $MRN_CND_SPY
		log "$MRN_CND_SPY output:_____________________________________________________________"
		cd $GIT_CLONE_DIR/$SERVICE_SRV_NAME && $MRN_CND_SPY install
		if [ $? -ne 0 ];then
			log "Install of \"$MRN_CND_SPY\" FAILS, exiting!!!"
			exit
		fi
	else
		log "$MRN_CND_SPY not found!"
	fi
# Creating etc directory for config files
	if [ ! -d $ETC_CFG_DIR ];then
		log "Creating $ETC_CFG_DIR direcory..."
		mkdir -p $ETC_CFG_DIR
		if [ $? -ne 0 ];then
			log "Can't create $ETC_CFG_DIR, exiting!!!"
			exit
		fi
	fi
# making sample configs 
	log "Making sample configuration files at \"$ETC_CFG_DIR\""
	for file in `ls $GIT_CLONE_DIR/$SERVICE_SRV_NAME/etc`
	do
		cp -f "$GIT_CLONE_DIR/$SERVICE_SRV_NAME/etc/$file" "$ETC_CFG_DIR/$file.sample"
	done
}

# inject init
injectinit()
{
ln -s /lib/init/upstart-job /etc/init.d/$SERVICE_SRV_NAME
echo "description \"$SERVICE_SRV_NAME service\"
author \"Igor Yozhikov <iyozhikov@mirantis.com>\"
start on runlevel [2345]
stop on runlevel [!2345]
respawn
env PYTHONPATH=\$PYTHONPATH:$GIT_CLONE_DIR/$SERVICE_SRV_NAME
export PYTHONPATH
exec start-stop-daemon --start --chuid root --user root --name $SERVICE_SRV_NAME --exec $SERVICE_EXEC_PATH -- --config-file=$SERVICE_CONFIG_FILE_PATH" > "/etc/init/$SERVICE_SRV_NAME.conf"
log "Reloading initctl"
initctl reload-configuration
update-rc.d $SERVICE_SRV_NAME defaults
}

# purge init
purgeinit()
{
	update-rc.d -f $SERVICE_SRV_NAME remove
	rm -f /etc/init.d/$SERVICE_SRV_NAME
	rm -f /etc/init/$SERVICE_SRV_NAME.conf
	log "Reloading initctl"
	initctl reload-configuration
}

# uninstall
uninst()
{
	rm -f $SERVICE_EXEC_PATH
	rm -rf $SERVICE_CONTENT_DIRECTORY
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
		# searching for daemon PATH
		if [ ! -x $SERVICE_EXEC_PATH ]; then
			log "Can't find \"$SERVICE_SRV_NAME\" in at \"$SERVICE_EXEC_PATH\", please install the \"$SERVICE_SRV_NAME\" or set variable SERVICE_EXEC_PATH=/path/to/daemon before running setup script, exiting!!!"
			exit
		fi
		log "Injecting \"$SERVICE_SRV_NAME\" to init..."
		injectinit
		postinst
		;;

	install )
		inst
		injectinit
		postinst
		;;

	installfromgit )
		inst "yes"
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
		echo "Usage: $(basename "$0") install | installfromgit | uninstall | inject-init | purge-init"
		exit 1
		;;
esac

