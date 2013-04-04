#!/bin/bash

if [[ -z "$1" ]] ; then
    SCRIPTS_DIR=$( cd $( dirname "$0" ) && pwd )
    source $SCRIPTS_DIR/localrc
fi


function glance_image_create {
    local __image_path=$1

    if [[ -z "$__image_path" ]] ; then
        echo "Image path is missed!"
        return
    fi

    local __image_name=${__image_path##*/}
    __image_name=${__image_name%.*}
    
    echo "Importing image '$__image_name' into Glance ..."
    glance image-delete "$__image_name"
    if [[ ^http =~ $__image_path]] ; then
        glance image-create \
          --name "$__image_name" \
          --disk-format qcow2 \
          --container-format bare \
          --is-public true \
          --copy-from "$__image_path"
    else
        glance image-create \
          --name "$__image_name" \
          --disk-format qcow2 \
          --container-format bare \
          --is-public true \
          --file "$__image_path"
    fi
}

# Executing post-stack actions
#===============================================================================

if [[ ,$INSTALL_MODE, =~ ',standalone,compute,' ]] ; then
    echo "Adding iptables rule to allow Internet access from instances..."
    __iptables_rule="POSTROUTING -t nat -s '$FIXED_RANGE' ! -d '$FIXED_RANGE' -j MASQUERADE"
    sudo iptables -C $__iptables_rule
    if [[ $? == 0 ]] ; then
        echo "Iptables rule already exists."
    else
        sudo iptables -A $__iptables_rule
    fi
fi


if [[ $INSTALL_MODE == 'compute' ]] ; then
    return
fi


if [[ -z "$(sudo rabbitmqctl list_users | grep keero)" ]] ; then
    echo "Adding RabbitMQ 'keero' user"
    sudo rabbitmqctl add_user keero keero
else
    echo "User 'Keero' already exists."
fi


if [[ -z "$(sudo rabbitmq-plugins list -e | grep rabbitmq_management)" ]] ; then
    echo "Enabling RabbitMQ management plugin"
    sudo rabbitmq-plugins enable rabbitmq_management
    
    echo "Restarting RabbitMQ ..."
    restart_service rabbitmq-server
else
    echo "RabbitMQ management plugin already enabled."
fi


echo "* Removing nova flavors ..."
for id in $(nova flavor-list | awk '$2 ~ /[[:digit:]]/ {print $2}') ; do
    echo "** Removing flavor '$id'"
    nova flavor-delete $id
done


echo "* Creating new flavors ..."
nova flavor-create m1.small  auto 768  40 1
nova flavor-create m1.medium auto 1024 40 1
nova flavor-create m1.large  auto 1280 40 2


echo "* Creating security group rules ..."
nova secgroup-add-rule default tcp 1 65535 0.0.0.0/0
nova secgroup-add-rule default udp 1 65535 0.0.0.0/0
nova secgroup-add-rule default icmp 0 8 0.0.0.0/0


if [[ -z "$(nova keypair-list | grep keero_key)" ]] ; then
    echo "Creating keypair 'keero_key' ..."
    nova keypair-add keero_key
else
    echo "Keypair 'keero_key' already exists"
fi

#===============================================================================

for $image in $GLANCE_IMAGE_LIST ; do
    glance_image_create "$image"
done

