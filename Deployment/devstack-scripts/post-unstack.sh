#!/bin/bash

if [[ -z "$1" ]] ; then
    source ./localrc
fi


#Remove certificates
echo "* Removing old certificate files"
for file in $(sudo find $DEVSTACK_DIR/accrc/ -type f -regex ".+.pem.*") ; do
    echo "Removing file '$file'"
    sudo rm -f "$file"
done

# Remove logs
echo Removing 'devstack' logs
sudo rm -f /var/log/devstack/*
#sudo rm -f /opt/stack/devstack/stack.sh.log

echo "* Removing 'apache2' logs"
for file in $(sudo find /var/log/apache2 -type f) ; do
    echo "Removing file '$file'"
    sudo rm -f "$file"
done

