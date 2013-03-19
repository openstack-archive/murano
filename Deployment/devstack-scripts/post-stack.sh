#!/bin/bash

if [ -z "$1" ] ; then
    source ./localrc
fi


function glance_image_create {
    local __image_name=$1

    if [[ -z "$__image_name" ]] ; then
        echo "No image name provided!"
        return
    fi

    echo "Importing image '$__image_name' into Glance..."
    glance image-delete "$__image_name"
    glance image-create \
      --name "$__image_name" \
      --disk-format qcow2 \
      --container-format bare \
      --is-public true \
      --copy-from "http://172.18.124.100:8888/$__image_name.qcow2"
}


# Executing post-stack actions
#===============================================================================

if [ -z "$(sudo rabbitmqctl list_users | grep keero)" ] ; then
    echo "Adding RabbitMQ 'keero' user"
    sudo rabbitmqctl add_user keero keero
else
    echo "User 'Keero' already exists."
fi


if [ -z "$(sudo rabbitmq-plugins list -e | grep rabbitmq_management)" ] ; then
    echo "Enabling RabbitMQ management plugin"
    sudo rabbitmq-plugins enable rabbitmq_management
else
    echo "RabbitMQ management plugin already enabled."
fi


echo "Restarting RabbitMQ ..."
restart_service rabbitmq-server


echo "* Removing nova flavors ..."
for id in $(nova flavor-list | awk '$2 ~ /[[:digit:]]/ {print $2}') ; do
    echo "** Removing flavor '$id'"
    nova flavor-delete $id
done


echo "* Creating new flavors ..."
nova flavor-create m1.small  auto 1024 40 1
nova flavor-create m1.medium auto 2048 40 2
nova flavor-create m1.large  auto 4096 40 4


if [ -z "$(nova keypair-list | grep keero_key)" ] ; then
    echo "Creating keypair 'keero_key' ..."
    nova keypair-add keero_key
else
    echo "Keypair 'keero_key' already exists"
fi

#===============================================================================

glance_image_create "ws-2012-full"
