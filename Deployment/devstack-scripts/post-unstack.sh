#!/bin/bash

if [[ -z "$1" ]] ; then
    SCRIPTS_DIR=$( cd $( dirname "$0" ) && pwd )
    source $SCRIPTS_DIR/localrc
fi


#Remove certificates
echo "* Removing old certificate files"
for file in $(sudo find $DEVSTACK_DIR/accrc/ -type f -regex ".+.pem.*") ; do
    echo "Removing file '$file'"
    sudo rm -f "$file"
done


# Remove logs
echo "* Removing 'devstack' logs ..."
sudo rm -f /opt/stack/log/*


echo "* Removing 'apache2' logs ..."
for file in $(sudo find /var/log/apache2 -type f) ; do
    echo "Removing file '$file'"
    sudo rm -f "$file"
done


echo "* Stopping all VMs ..."
sudo killall kvm
sleep 2


echo "* Unmounting ramdrive ..."
umount /opt/stack/data/nova/instances

