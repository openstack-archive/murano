#!/bin/bash

SCRIPTS_DIR=$( cd $( dirname "$0" ) && pwd )

source $SCRIPTS_DIR/localrc

groupadd stack
useradd -g stack -s /bin/bash -m stack

echo 'stack ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/stack
chmod 0440 /etc/sudoers.d/stack

mkdir -p $DEVSTACK_INSTALL_DIR
chmod stack:stack $DEVSTACK_INSTALL_DIR

sudo -u stack << EOF
cd
rm -rf devstack
git clone git://github.com/openstack-dev/devstack.git
EOF

