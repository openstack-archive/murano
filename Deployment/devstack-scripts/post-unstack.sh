#!/bin/bash

source openrc admin admin

if [ -z "$TOP_DIR" ] ; then
    echo "Environment variable TOP_DIR is not set."
    exit
fi

echo "Devstack installed in '$TOP_DIR'"

#Remove certificates
echo "* Removing certificate files ..."
for file in $(sudo find $TOP_DIR/accrc/ -type f -regex ".+.pem.*") ; do
    echo "Removing file '$file'"
    sudo rm -f "$file"
done

# Remove logs
echo "* Removing 'devstack' logs ..."
sudo rm -f /var/log/devstack/*


echo "* Removing 'apache2' logs ..."
for file in $(sudo find /var/log/apache2 -type f) ; do
    echo "Removing file '$file'"
    sudo rm -f "$file"
done
