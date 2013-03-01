#!/bin/bash

source openrc admin admin

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
sudo service rabbitmq-server restart


echo "* Removing nova flavors ..."
for id in $(nova flavor-list | awk '$2 ~ /[[:digit:]]/ {print $2}') ; do
    echo "** Removing flavor '$id'"
    nova flavor-delete $id
done


echo "* Creating new flavors ..."
nova flavor-create m1.small  auto 2048 40 1
nova flavor-create m1.medium auto 4096 60 2
nova flavor-create m1.large  auto 8192 80 4


if [ -z "$(nova keypair-list | grep keero_key)" ] ; then
    echo "Creating keypair 'keero_key' ..."
    nova keypair-add keero_key
else
    echo "Keypair 'keero_key' already exists"
fi


echo "Removing existing image"
glance image-delete ws-2012-full-agent


echo "* Importing image into glance ..."
glance image-create \
  --name ws-2012-full-agent \
  --disk-format qcow2 \
  --container-format ovf \
  --is-public true \
  --location http://172.18.124.100:8888/ws-2012-full-agent.qcow2
#  --file /opt/keero/iso/ws-2012-full-agent.qcow2
